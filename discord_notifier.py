import discord
from discord.ext import commands
import config
import logging
import traceback
import asyncio

class DiscordNotifier:
    def __init__(self):
        logging.info("Initializing Discord notifier")
        if not config.DISCORD_TOKEN:
            logging.error("Discord token is not set in environment variables")
            raise ValueError("Discord token is required")
        if not config.DISCORD_CHANNEL_ID:
            logging.error("Discord channel ID is not set in environment variables")
            raise ValueError("Discord channel ID is required")
            
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)
        self.channel = None
        self.ready = asyncio.Event()

        @self.client.event
        async def on_ready():
            logging.info(f"Logged in as {self.client.user}")
            self.channel = self.client.get_channel(config.DISCORD_CHANNEL_ID)
            if not self.channel:
                logging.error(f"Could not find Discord channel with ID: {config.DISCORD_CHANNEL_ID}")
            self.ready.set()

    async def connect(self):
        """Connect to Discord and get the channel."""
        logging.info(f"Attempting to connect to Discord (Channel ID: {config.DISCORD_CHANNEL_ID})")
        try:
            # Start the client in the background
            asyncio.create_task(self.client.start(config.DISCORD_TOKEN))
            # Wait for the ready event
            await asyncio.wait_for(self.ready.wait(), timeout=30)
            
            if not self.channel:
                return False
                
            logging.info(f"Successfully found Discord channel: {self.channel.name}")
            return True
            
        except asyncio.TimeoutError:
            logging.error("Timeout waiting for Discord connection")
            return False
        except Exception as e:
            logging.error(f"Failed to connect to Discord: {str(e)}")
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def get_item_thumbnail(self, item):
        """Get the first image thumbnail URL for an item."""
        try:
            # Check for thumbnail_display_urls in the item data
            thumbnail_urls = item.get('thumbnail_display_urls', {})
            if thumbnail_urls:
                # Try to get medium size, fall back to large or small
                return (thumbnail_urls.get('medium') or 
                       thumbnail_urls.get('large') or 
                       thumbnail_urls.get('small'))
        except Exception as e:
            logging.error(f"Error getting thumbnail for item: {str(e)}")
        return None

    def get_item_description(self, item, max_length=200):
        """Extract and truncate item description."""
        try:
            # Try to get description from dcterms:description
            description = item.get('dcterms:description', [])
            if description and isinstance(description, list) and len(description) > 0:
                # Get the first description value
                desc_value = description[0].get('@value', '')
                if desc_value:
                    if len(desc_value) > max_length:
                        return desc_value[:max_length] + '...'
                    return desc_value
            
            # Fallback to checking other potential description fields
            alt_fields = ['bibo:content', 'o:description']
            for field in alt_fields:
                desc = item.get(field, [])
                if desc and isinstance(desc, list) and len(desc) > 0:
                    desc_value = desc[0].get('@value', '')
                    if desc_value:
                        if len(desc_value) > max_length:
                            return desc_value[:max_length] + '...'
                        return desc_value
            
            return "No description available"
            
        except Exception as e:
            logging.error(f"Error getting description for item: {str(e)}")
            return "Error retrieving description"

    def get_item_format(self, item):
        """Extract format information from item."""
        try:
            # Try dcterms:format first
            format_info = item.get('dcterms:format', [])
            if format_info and isinstance(format_info, list) and len(format_info) > 0:
                return format_info[0].get('@value', '')

            # Try alternative format fields
            alt_fields = ['dcterms:type', 'o:media_type']
            for field in alt_fields:
                format_info = item.get(field, [])
                if format_info and isinstance(format_info, list) and len(format_info) > 0:
                    return format_info[0].get('@value', '')
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting format for item: {str(e)}")
            return None

    async def send_notification(self, items):
        """Send notification about new items to Discord."""
        if not items:
            logging.info("No items to send to Discord")
            return

        logging.info(f"Preparing Discord message for {len(items)} items")
        
        try:
            # Split items into chunks of 9
            for i in range(0, len(items), 9):
                chunk = items[i:i+9]
                chunk_number = i // 9 + 1
                total_chunks = (len(items) + 8) // 9

                header_embed = discord.Embed(
                    title="Recently added items in our Archive",
                    color=discord.Color.blue(),
                    url="https://archive.hitsave.org"
                )

                if total_chunks == 1:
                    if len(items) == 1:
                        footer_text = "1 new item found"
                    else:
                        footer_text = f"{len(items)} new items found"
                else:
                    footer_text = f"Message {chunk_number} of {total_chunks} - Items {i+1}-{min(i+9, len(items))} of {len(items)}"
                
                header_embed.set_footer(text=footer_text)
                
                embeds = []
                for item in chunk:
                    title = item.get('o:title', 'Untitled')
                    item_id = item.get('o:id', 'Unknown ID')
                    ark_url = f"https://archive.hitsave.org/ark:/78322/{item_id}"
                    
                    embed = discord.Embed(
                        title=title,
                        url=ark_url,
                        color=discord.Color.blue()
                    )
                    
                    # Add description
                    description = self.get_item_description(item)
                    embed.description = description

                    # Add format information if available
                    format_info = self.get_item_format(item)
                    if format_info:
                        embed.set_footer(text=format_info)

                    # Add thumbnail if available
                    thumbnail_url = self.get_item_thumbnail(item)
                    if thumbnail_url:
                        embed.set_thumbnail(url=thumbnail_url)

                    embeds.append(embed)

                await self.channel.send(embeds=[header_embed, *embeds])
                logging.info(f"Successfully sent Discord message chunk {chunk_number} of {total_chunks}")
                
                if chunk_number < total_chunks:
                    await asyncio.sleep(1)
            
        except Exception as e:
            logging.error(f"Failed to send Discord notification: {str(e)}")
            logging.error(f"Full traceback: {traceback.format_exc()}")

    async def close(self):
        """Close the Discord connection."""
        try:
            logging.info("Closing Discord connection")
            await self.client.close()
            logging.info("Discord connection closed successfully")
        except Exception as e:
            logging.error(f"Error closing Discord connection: {str(e)}") 