#!/command/with-contenv bash
set -e

echo "[init] Configuring Wallos..."

# Read timezone from options
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.TZ // "Europe/Berlin"' /data/options.json)
    export TZ
    echo "[init] Timezone set to: ${TZ}"
fi

# Set up persistent storage
mkdir -p /data/db /data/logos

# Initialize database on first run
if [ ! -f /data/db/wallos.db ]; then
    echo "[init] First run - initializing database"

    # Copy empty database from Wallos repo if it exists
    if [ -f /var/www/html/db/wallos.empty.db ]; then
        echo "[init] Copying empty database template"
        cp /var/www/html/db/wallos.empty.db /data/db/wallos.db
    else
        echo "[init] No empty database found, will create on first access"
    fi
fi

# Copy initial logos if they exist and target is empty
if [ -d /var/www/html/images/uploads/logos ] && [ ! "$(ls -A /data/logos 2>/dev/null)" ]; then
    echo "[init] Copying initial logos"
    cp -rn /var/www/html/images/uploads/logos/. /data/logos/ 2>/dev/null || true
fi

# Create directories if they don't exist in the image
mkdir -p /var/www/html/images/uploads

# Remove original directories and create symlinks
rm -rf /var/www/html/db /var/www/html/images/uploads/logos
ln -s /data/db /var/www/html/db
ln -s /data/logos /var/www/html/images/uploads/logos

# Set ownership and permissions
chown -R www-data:www-data /data/db /data/logos
chmod -R 775 /data/db/
mkdir -p /var/www/html/images/uploads/logos/avatars
chmod -R 775 /data/logos/

echo "[init] Persistent storage ready"

# Initialize and migrate database
echo "[init] Creating database if needed"
/usr/local/bin/php /var/www/html/endpoints/cronjobs/createdatabase.php

echo "[init] Running database migrations"
/usr/local/bin/php /var/www/html/endpoints/db/migrate.php

echo "[init] Database initialization complete"

# Run initial cron jobs
echo "[init] Running initial cron jobs"
/usr/local/bin/php /var/www/html/endpoints/cronjobs/updatenextpayment.php 2>/dev/null || true
/usr/local/bin/php /var/www/html/endpoints/cronjobs/updateexchange.php 2>/dev/null || true
/usr/local/bin/php /var/www/html/endpoints/cronjobs/checkforupdates.php 2>/dev/null || true

echo "[init] Wallos initialization complete"
