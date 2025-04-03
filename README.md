# Omeka S Daily Checker

This script checks the Omeka S API daily for new items with media attachments and sends notifications to a Discord channel. It will look back up to 30 days to find enough items if there aren't enough recent additions.

## Features

- Checks Omeka S API for new items with media attachments
- Sends notifications to Discord with thumbnails and ARK identifiers
- Looks back up to 30 days to find at least 9 items
- Supports both Docker and local deployment
- Comprehensive logging system
- Automatic daily checks via cron (in Docker)

## Setup

### Local Setup
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your Discord credentials:
```bash
cp .env.example .env
```

Required environment variables:
- `DISCORD_TOKEN`: Your Discord bot token
- `DISCORD_CHANNEL_ID`: The channel ID where notifications should be sent

### Docker Setup
1. Copy `.env.example` to `.env` and fill in your Discord credentials:
```bash
cp .env.example .env
```

2. Build and run the container:
```bash
docker compose up -d
```

## Usage

### Local Usage
Run the script manually:
```bash
python omeka_checker.py
```

### Docker Usage
The container will automatically run the check daily at 8 AM UTC. 

To run a manual check:
```bash
docker compose exec omeka-checker python omeka_checker.py
```

## Logging

The script creates log files in the `logs` directory:
- `omeka_updates.log`: Contains information about new items and script execution
- `cron.log`: Contains cron job execution logs (Docker only)

Log information for each item includes:
- Item ID
- Title
- ARK identifier
- Creation date
- Media thumbnail URL

## Discord Notifications

Discord messages include:
- Thumbnail preview of the first media item
- Item title
- ARK identifier (clickable link)
- Pagination for more than 9 items
- Total count of new items found

## Development

To rebuild the container after making changes:
```bash
docker compose build --no-cache
docker compose up -d
```

## Configuration

The script can be configured through the following files:
- `config.py`: API URLs and logging settings
- `docker/crontab`: Schedule for automatic checks (Docker only)
- `.env`: Discord credentials and other sensitive settings

## Error Handling

The script includes comprehensive error handling for:
- API connection issues
- Discord connectivity problems
- Missing or invalid credentials
- Rate limiting
- Media attachment processing

## Requirements

- Python 3.11+
- Discord bot with proper permissions
- Access to Omeka S API
- Docker (optional)

## Notes

- The script will look back up to 30 days to find at least 9 items with media
- Discord messages are split into chunks of 9 items each to stay within Discord's embed limits
- All sensitive information should be stored in the `.env` file
- The `.env` file is excluded from git via `.gitignore` 