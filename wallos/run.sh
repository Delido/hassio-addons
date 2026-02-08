#!/bin/sh

# Read options from Home Assistant
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.TZ // "Europe/Berlin"' /data/options.json)
    EXTERNAL_PORT=$(jq -r '.external_port // 3422' /data/options.json)
    export TZ
fi

echo "[Wallos] Starting with timezone: ${TZ}"
echo "[Wallos] External port: ${EXTERNAL_PORT}"

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

# Set ownership and permissions before initialization
chown -R www-data:www-data /data/db /data/logos
chmod -R 775 /data/db/
mkdir -p /var/www/html/images/uploads/logos/avatars
chmod -R 775 /data/logos/

echo "[Wallos] Persistent storage ready"

# Initialize and migrate database BEFORE starting services
echo "[Wallos] Creating database if needed"
/usr/local/bin/php /var/www/html/endpoints/cronjobs/createdatabase.php

echo "[Wallos] Running database migrations"
/usr/local/bin/php /var/www/html/endpoints/db/migrate.php

echo "[Wallos] Database initialization complete"

# Configure nginx to listen on external port
echo "[Wallos] Configuring nginx for external port ${EXTERNAL_PORT}"
cat > /etc/nginx/http.d/external.conf <<EOF
server {
    listen ${EXTERNAL_PORT};
    root /var/www/html;
    index index.php index.html;

    location / {
        try_files \$uri \$uri/ /index.php?\$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
    }
}
EOF

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

# Run initial cron jobs
/usr/local/bin/php /var/www/html/endpoints/cronjobs/updatenextpayment.php 2>/dev/null || true
/usr/local/bin/php /var/www/html/endpoints/cronjobs/updateexchange.php 2>/dev/null || true
/usr/local/bin/php /var/www/html/endpoints/cronjobs/checkforupdates.php 2>/dev/null || true

echo "[Wallos] All services started successfully"

# Wait for all child processes
wait
