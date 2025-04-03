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

def get_items_with_media(start_date, end_date, min_items=9):
    """Fetch items with media between dates from Omeka S API."""
    headers = {
        'Content-Type': 'application/json'
    }
    
    url = f"{config.OMEKA_API_URL}/items"
    params = {
        'created_after': start_date.isoformat(),
        'created_before': end_date.isoformat(),
        'has_media': '1'  # Filter for items with media
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        items = response.json()
        
        if items and len(items) >= min_items:
            logging.info(f"Found {len(items)} items with media between {start_date} and {end_date}")
            return items
        
        # If we don't have enough items, look back one more day
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
        if start_date > thirty_days_ago:  # Limit to 30 days lookback
            logging.info(f"Only found {len(items) if items else 0} items, checking previous day")
            new_end_date = start_date
            new_start_date = start_date - timedelta(days=1)
            previous_items = get_items_with_media(new_start_date, new_end_date, min_items)
            
            # Combine items from both periods
            if previous_items:
                items = (items or []) + previous_items
            
        return items
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching items from Omeka S API: {str(e)}")
        return None

def get_today_items():
    """Fetch items added today from Omeka S API."""
    # Ensure we're working with date objects consistently
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    items = get_items_with_media(today, tomorrow)
    
    if not items:
        logging.info("No items found for today")
        return None
        
    logging.info(f"Found total of {len(items)} items with media")
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
    logging.info("Starting Omeka S daily check")
    
    try:
        items = get_today_items()
        if items is None:
            logging.error("Failed to fetch items from Omeka S API")
            return
            
        logging.info(f"Found {len(items) if items else 0} items")
        log_new_items(items)
        
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
        else:
            logging.info("No items to send to Discord")
            
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        logging.error(f"Full traceback: {traceback.format_exc()}")
    
    logging.info("Completed Omeka S daily check")

if __name__ == "__main__":
    asyncio.run(main()) 