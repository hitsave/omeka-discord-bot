# Omeka S Daily Checker

This script checks the Omeka S API for new items with media attachments from the last 24 hours and sends notifications to a Discord channel. When enabled, it can look back through previous days if not enough recent items are found.

## Features

- Checks Omeka S API for items added in the last 24 hours
- Only includes items with media attachments
- Excludes items with placeholder descriptions
- Sends notifications to Discord with:
  - Thumbnails
  - Descriptions
  - Format information (DVD, VHS, Magazine, etc.)
- Optional lookback feature for quiet periods
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

### Docker Setup
1. Copy `.env.example` to `.env` and fill in your Discord credentials:
```bash
cp .env.example .env
```

2. Build and run the container:
```bash
docker compose up -d
```

## Configuration

### Required Settings
- `DISCORD_TOKEN`: Your Discord bot token
- `DISCORD_CHANNEL_ID`: The channel ID where notifications should be sent

### Optional Settings
- `ENABLE_LOOKBACK`: Set to "true" to enable looking back through previous days (default: "false")
- `LOOKBACK_MIN_ITEMS`: Minimum number of items to find when lookback is enabled (default: 9)

## Time Windows

### Default Behavior
- Checks for items added in the last 24 hours from the time of execution
- For example, if run at 3 PM, checks from 3 PM yesterday to 3 PM today
- Skips Discord notification if no new items are found
- Does not look back to previous days

### Lookback Mode
When `ENABLE_LOOKBACK` is set to "true":
1. First checks the last 24 hours for new items
2. If fewer than `LOOKBACK_MIN_ITEMS` are found, checks the previous 24-hour period
3. Continues looking back up to 30 days until enough items are found
4. Each lookback period is a full 24 hours

## Usage

### Local Usage
Run the script manually:
```bash
python omeka_checker.py
```

### Docker Usage
The container will automatically run the check daily at 8 AM UTC. Each check will look for items added in the previous 24 hours.

To run a manual check:
```bash
docker compose exec omeka-checker python omeka_checker.py
```

## Logging

The script creates log files in the `logs` directory:
- `omeka_updates.log`: Contains information about new items and script execution
- `cron.log`: Contains cron job execution logs (Docker only)

Log information includes:
- Number of items found in each time period
- Items excluded due to placeholder descriptions
- Format and media information
- Discord notification status

## Discord Notifications

Each notification includes:
- Thumbnail preview of the first media item
- Item title (clickable link)
- Description (truncated if too long)
- Format information (e.g., DVD, VHS, Magazine)
- Pagination for more than 9 items per message

## Development

To rebuild the container after making changes:
```bash
docker compose build --no-cache
docker compose up -d
```

## Requirements

- Python 3.11+
- Discord bot with proper permissions
- Access to Omeka S API
- Docker (optional)

## Notes

- The script uses rolling 24-hour windows rather than calendar days
- All times are in UTC to ensure consistency
- The lookback feature is disabled by default
- Items with placeholder descriptions are automatically excluded 