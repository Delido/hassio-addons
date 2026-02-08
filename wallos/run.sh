#!/bin/sh

# Read timezone from Home Assistant options
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.TZ // "Europe/Berlin"' /data/options.json)
    export TZ
fi

echo "[Wallos] Starting with timezone: ${TZ}"

# Set up persistent storage
mkdir -p /data/db /data/logos

# Initialize database on first run
if [ ! -f /data/db/wallos.db ]; then
    echo "[Wallos] First run - initializing database"

    # Copy empty database from Wallos repo if it exists
    if [ -f /var/www/html/db/wallos.empty.db ]; then
        echo "[Wallos] Copying empty database template"
        cp /var/www/html/db/wallos.empty.db /data/db/wallos.db
    else
        echo "[Wallos] No empty database found, will create on first access"
    fi
fi

# Copy initial logos if they exist and target is empty
if [ -d /var/www/html/images/uploads/logos ] && [ ! "$(ls -A /data/logos 2>/dev/null)" ]; then
    echo "[Wallos] Copying initial logos"
    cp -rn /var/www/html/images/uploads/logos/. /data/logos/ 2>/dev/null || true
fi

# Create directories if they don't exist in the image
mkdir -p /var/www/html/images/uploads

# Remove original directories and create symlinks
rm -rf /var/www/html/db /var/www/html/images/uploads/logos
ln -s /data/db /var/www/html/db
ln -s /data/logos /var/www/html/images/uploads/logos

echo "[Wallos] Persistent storage ready"

# Start PHP-FPM, Crond, and Nginx (like original startup.sh)
echo "Launching php-fpm"
php-fpm -F &
PHP_FPM_PID=$!

echo "Launching crond"
crond -f &
CROND_PID=$!

echo "Launching nginx"
nginx -g 'daemon off;' &
NGINX_PID=$!

# Wait for services to start
sleep 1

# Initialize database if needed
/usr/bin/php /var/www/html/endpoints/cronjobs/createdatabase.php 2>/dev/null || true
/usr/bin/php /var/www/html/endpoints/db/migrate.php 2>/dev/null || true

# Set permissions
chmod -R 755 /var/www/html/db/ 2>/dev/null || true
mkdir -p /var/www/html/images/uploads/logos/avatars 2>/dev/null || true
chmod -R 755 /var/www/html/images/uploads/logos 2>/dev/null || true

# Run initial cron jobs
/usr/bin/php /var/www/html/endpoints/cronjobs/updatenextpayment.php 2>/dev/null || true
/usr/bin/php /var/www/html/endpoints/cronjobs/updateexchange.php 2>/dev/null || true
/usr/bin/php /var/www/html/endpoints/cronjobs/checkforupdates.php 2>/dev/null || true

echo "[Wallos] All services started successfully"

# Wait for all child processes
wait
