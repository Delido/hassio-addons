#!/command/with-contenv bash

echo "[wallos-init] Configuring Wallos..."

# Read timezone from options
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.TZ // "Europe/Berlin"' /data/options.json)
    export TZ
    echo "[wallos-init] Timezone set to: ${TZ}"
fi

SHARE_DB="/share/wallos/db"
SHARE_LOGOS="/share/wallos/logos"
APP_DB="/var/www/html/db"
APP_LOGOS="/var/www/html/images/uploads/logos"

# --- Persistent storage setup ---
echo "[wallos-init] Setting up persistent storage in /share/wallos..."
mkdir -p "${SHARE_DB}" "${SHARE_LOGOS}"

if [ ! -d "${SHARE_DB}" ]; then
    echo "[wallos-init] ERROR: Could not create ${SHARE_DB} - check /share mount"
    exit 1
fi

# Copy database template on first run
if [ ! -f "${SHARE_DB}/wallos.db" ]; then
    echo "[wallos-init] First run - no database found in ${SHARE_DB}"
    if [ -f "${APP_DB}/wallos.empty.db" ]; then
        echo "[wallos-init] Copying empty database template"
        cp "${APP_DB}/wallos.empty.db" "${SHARE_DB}/wallos.db"
    else
        echo "[wallos-init] No template found, creating empty SQLite database"
        sqlite3 "${SHARE_DB}/wallos.db" "SELECT 1;" 2>/dev/null || touch "${SHARE_DB}/wallos.db"
    fi
fi

# Copy initial logos if target is empty
if [ -d "${APP_LOGOS}" ] && [ ! "$(ls -A "${SHARE_LOGOS}" 2>/dev/null)" ]; then
    echo "[wallos-init] Copying initial logos"
    cp -rn "${APP_LOGOS}/." "${SHARE_LOGOS}/" 2>/dev/null || true
fi

# --- Create symlinks from app dirs to persistent storage ---
echo "[wallos-init] Creating symlinks to persistent storage..."
mkdir -p /var/www/html/images/uploads

# Remove original dirs/old symlinks and create fresh symlinks
rm -rf "${APP_DB}"
rm -rf "${APP_LOGOS}"
ln -sf "${SHARE_DB}" "${APP_DB}"
ln -sf "${SHARE_LOGOS}" "${APP_LOGOS}"

# Verify symlinks
if [ ! -L "${APP_DB}" ] || [ "$(readlink "${APP_DB}")" != "${SHARE_DB}" ]; then
    echo "[wallos-init] ERROR: Symlink ${APP_DB} -> ${SHARE_DB} failed!"
    exit 1
fi
echo "[wallos-init] Symlink OK: ${APP_DB} -> $(readlink "${APP_DB}")"

# Set ownership and permissions
chown -R www-data:www-data "${SHARE_DB}" "${SHARE_LOGOS}" 2>/dev/null || true
chmod -R 775 "${SHARE_DB}" 2>/dev/null || true
mkdir -p "${APP_LOGOS}/avatars"
chmod -R 775 "${SHARE_LOGOS}" 2>/dev/null || true

echo "[wallos-init] Persistent storage ready"

# --- Database initialization ---
echo "[wallos-init] Running database creation..."
/usr/local/bin/php /var/www/html/endpoints/cronjobs/createdatabase.php 2>&1 || echo "[wallos-init] WARNING: createdatabase.php returned an error"

echo "[wallos-init] Running database migrations..."
/usr/local/bin/php /var/www/html/endpoints/db/migrate.php 2>&1 || echo "[wallos-init] WARNING: migrate.php returned an error"

# Verify database exists
if [ -f "${SHARE_DB}/wallos.db" ]; then
    DB_SIZE=$(stat -c%s "${SHARE_DB}/wallos.db" 2>/dev/null || echo "unknown")
    echo "[wallos-init] Database OK: ${SHARE_DB}/wallos.db (${DB_SIZE} bytes)"
else
    echo "[wallos-init] WARNING: Database not found after initialization!"
    echo "[wallos-init] Creating fallback empty database..."
    sqlite3 "${SHARE_DB}/wallos.db" "SELECT 1;" 2>/dev/null || touch "${SHARE_DB}/wallos.db"
    chown www-data:www-data "${SHARE_DB}/wallos.db" 2>/dev/null || true
    chmod 664 "${SHARE_DB}/wallos.db" 2>/dev/null || true
    # Re-run creation script
    /usr/local/bin/php /var/www/html/endpoints/cronjobs/createdatabase.php 2>&1 || true
fi

# Run initial cron jobs
echo "[wallos-init] Running initial cron jobs..."
/usr/local/bin/php /var/www/html/endpoints/cronjobs/updatenextpayment.php 2>/dev/null || true
/usr/local/bin/php /var/www/html/endpoints/cronjobs/updateexchange.php 2>/dev/null || true
/usr/local/bin/php /var/www/html/endpoints/cronjobs/checkforupdates.php 2>/dev/null || true

echo "[wallos-init] Wallos initialization complete"
