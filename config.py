import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Omeka S API Configuration
OMEKA_API_URL = "https://archive.hitsave.org/api"

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

# Logging Configuration
LOG_FILE = os.path.join("logs", "omeka_updates.log") 