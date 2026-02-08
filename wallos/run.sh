#!/bin/sh

# Read timezone from Home Assistant options
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.TZ // "Europe/Berlin"' /data/options.json)
    export TZ
fi

echo "[Wallos] Starting with timezone: ${TZ}"

# Set up persistent storage symlinks
mkdir -p /data/db /data/logos

# Migrate/link database directory
if [ ! -L /var/www/html/db ]; then
    if [ -d /var/www/html/db ] && [ "$(ls -A /var/www/html/db 2>/dev/null)" ]; then
        cp -rn /var/www/html/db/. /data/db/ 2>/dev/null || true
    fi
    rm -rf /var/www/html/db
    ln -s /data/db /var/www/html/db
fi

# Migrate/link logos directory
if [ ! -L /var/www/html/images/uploads/logos ]; then
    if [ -d /var/www/html/images/uploads/logos ] && [ "$(ls -A /var/www/html/images/uploads/logos 2>/dev/null)" ]; then
        cp -rn /var/www/html/images/uploads/logos/. /data/logos/ 2>/dev/null || true
    fi
    rm -rf /var/www/html/images/uploads/logos
    ln -s /data/logos /var/www/html/images/uploads/logos
fi

# Fix ownership
chown -R www-data:www-data /data/db /data/logos

echo "[Wallos] Persistent storage ready"

# Start Wallos (nginx + php-fpm via dumb-init)
exec /var/www/html/startup.sh
