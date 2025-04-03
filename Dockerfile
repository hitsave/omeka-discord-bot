FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Create a non-root user first
RUN useradd -m appuser

# Set up the cron job to run as appuser
COPY docker/crontab /etc/cron.d/omeka-checker
RUN chmod 0644 /etc/cron.d/omeka-checker && \
    crontab -u appuser /etc/cron.d/omeka-checker

# Set permissions after everything is set up
RUN chown -R appuser:appuser /app

# Run cron in the foreground as root
CMD ["cron", "-f"] 