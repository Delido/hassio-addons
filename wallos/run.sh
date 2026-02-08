#!/bin/sh

# Read timezone from Home Assistant options
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.TZ // "Europe/Berlin"' /data/options.json)
    export TZ
fi

echo "[Wallos] Starting with timezone: ${TZ}"

# Set up persistent storage
mkdir -p /data/db /data/logos

# Only migrate existing data on first run, then use bind mounts
if [ ! -f /data/db/.initialized ]; then
    echo "[Wallos] First run - initializing persistent storage"

    # Copy initial database if it exists in the image
    if [ -d /var/www/html/db ] && [ "$(ls -A /var/www/html/db 2>/dev/null)" ]; then
        cp -rn /var/www/html/db/. /data/db/ 2>/dev/null || true
    fi

    # Copy initial logos if they exist in the image
    if [ -d /var/www/html/images/uploads/logos ] && [ "$(ls -A /var/www/html/images/uploads/logos 2>/dev/null)" ]; then
        cp -rn /var/www/html/images/uploads/logos/. /data/logos/ 2>/dev/null || true
    fi

    touch /data/db/.initialized
fi

# Create directories if they don't exist in the image
mkdir -p /var/www/html/images/uploads

# Remove original directories and create symlinks
rm -rf /var/www/html/db /var/www/html/images/uploads/logos
ln -s /data/db /var/www/html/db
ln -s /data/logos /var/www/html/images/uploads/logos

echo "[Wallos] Persistent storage ready"

# Start Apache with PHP (default command in bellamy/wallos image)
exec apache2-foreground
