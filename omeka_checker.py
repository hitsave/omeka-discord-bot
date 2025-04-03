import requests
import logging
import asyncio
from datetime import datetime, timedelta
from dateutil import parser
import config
from discord_notifier import DiscordNotifier
import traceback

# Set up logging with more detailed format
logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Add console logging as well
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

def should_include_item(item):
    """Check if an item should be included in Discord notifications."""
    try:
        # Check description fields
        description = item.get('dcterms:description', [])
        if description and isinstance(description, list) and len(description) > 0:
            desc_value = description[0].get('@value', '')
            logging.debug(f"Found description: {desc_value[:100]}...")  # Log first 100 chars
            if desc_value.startswith("More information to be added at a later date."):
                logging.info(f"Excluding item {item.get('o:id', 'unknown')} due to placeholder description")
                return False
        
        # Check alternative description fields
        alt_fields = ['bibo:content', 'o:description']
        for field in alt_fields:
            desc = item.get(field, [])
            if desc and isinstance(desc, list) and len(desc) > 0:
                desc_value = desc[0].get('@value', '')
                logging.debug(f"Found {field} description: {desc_value[:100]}...")  # Log first 100 chars
                if desc_value.startswith("More information to be added at a later date."):
                    logging.info(f"Excluding item {item.get('o:id', 'unknown')} due to placeholder {field}")
                    return False
        
        # Log the raw description data for debugging
        logging.debug(f"Raw item description data: {item.get('dcterms:description', [])}")
        return True
        
    except Exception as e:
        logging.error(f"Error checking item description: {str(e)}")
        return True  # Include item if there's an error checking description

def get_items_with_media(start_datetime, end_datetime, enable_lookback=False, min_items=None):
    """Fetch items with media between dates from Omeka S API."""
    headers = {
        'Content-Type': 'application/json'
    }
    
    url = f"{config.OMEKA_API_URL}/items"
    params = {
        'created_after': start_datetime.isoformat(),
        'created_before': end_datetime.isoformat(),
        'has_media': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        all_items = response.json()
        
        # Filter out items with placeholder descriptions
        if all_items:
            items = [item for item in all_items if should_include_item(item)]
            filtered_count = len(all_items) - len(items)
            if filtered_count > 0:
                logging.info(f"Filtered out {filtered_count} items with placeholder descriptions")
        else:
            items = []
        
        # If lookback is enabled and we don't have enough items
        if (enable_lookback and min_items and 
            items and len(items) < min_items and 
            start_datetime > (datetime.now() - timedelta(days=30))):
            
            logging.info(f"Only found {len(items)} items, checking previous day (lookback enabled)")
            new_end_datetime = start_datetime
            new_start_datetime = start_datetime - timedelta(days=1)
            previous_items = get_items_with_media(new_start_datetime, new_end_datetime, 
                                                enable_lookback=True, 
                                                min_items=min_items)
            
            if previous_items:
                items = (items or []) + previous_items
        
        return items
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching items from Omeka S API: {str(e)}")
        return None

def get_recent_items():
    """Fetch items added in the last 24 hours."""
    now = datetime.now()
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    items = get_items_with_media(
        twenty_four_hours_ago, 
        now,
        enable_lookback=config.ENABLE_LOOKBACK,
        min_items=config.LOOKBACK_MIN_ITEMS if config.ENABLE_LOOKBACK else None
    )
    
    if not items:
        logging.info("No new items found in the last 24 hours")
        return None
        
    if config.ENABLE_LOOKBACK:
        logging.info(f"Found total of {len(items)} items with media (lookback enabled)")
    else:
        logging.info(f"Found {len(items)} new items with media in the last 24 hours")
    
    return items

def log_new_items(items):
    """Log new items to the log file."""
    if not items:
        logging.info("No new items found for today")
        return
    
    logging.info(f"Found {len(items)} new items for today")
    for item in items:
        item_id = item.get('o:id', 'Unknown ID')
        title = item.get('o:title', 'Untitled')
        created = item.get('o:created', 'Unknown date')
        
        try:
            created_date = parser.parse(created).strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_date = created
            
        logging.info(f"Item ID: {item_id}, Title: {title}, Created: {created_date}")

def get_item_thumbnail(item):
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

async def main():
    """Main function to check for new items and send notifications."""
    logging.info("Starting Omeka S check")
    
    try:
        items = get_recent_items()  # Changed from get_today_items()
        if items:
            logging.info("Initializing Discord notification")
            try:
                notifier = DiscordNotifier()
                if await notifier.connect():
                    await notifier.send_notification(items)
                    await notifier.close()
                else:
                    logging.error("Failed to connect to Discord")
            except Exception as e:
                logging.error(f"Discord notification failed: {str(e)}")
                logging.error(f"Full traceback: {traceback.format_exc()}")
        
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        logging.error(f"Full traceback: {traceback.format_exc()}")
    
    logging.info("Completed Omeka S check")

if __name__ == "__main__":
    asyncio.run(main()) 