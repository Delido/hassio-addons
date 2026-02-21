#!/command/with-contenv bash
set -e

echo "[minio-init] Configuring MinIO..."

# Read configuration from options.json
if [ -f /data/options.json ]; then
    TZ=$(jq -r '.timezone // "Europe/Berlin"' /data/options.json 2>/dev/null || echo "Europe/Berlin")
    MINIO_USER=$(jq -r '.username // "minioadmin"' /data/options.json 2>/dev/null || echo "minioadmin")
    MINIO_PASS=$(jq -r '.password // "minioadmin"' /data/options.json 2>/dev/null || echo "minioadmin")
else
    TZ="Europe/Berlin"
    MINIO_USER="minioadmin"
    MINIO_PASS="minioadmin"
fi

# Set timezone
ln -sf "/usr/share/zoneinfo/${TZ}" /etc/localtime 2>/dev/null || true
echo "${TZ}" > /etc/timezone 2>/dev/null || true
echo "[minio-init] Timezone set to: ${TZ}"

# Export environment variables for MinIO service via s6-overlay
mkdir -p /var/run/s6/container_environment
printf "%s" "${MINIO_USER}" > /var/run/s6/container_environment/MINIO_ROOT_USER
printf "%s" "${MINIO_PASS}" > /var/run/s6/container_environment/MINIO_ROOT_PASSWORD
# Create persistent data directory in /data
echo "[minio-init] Setting up persistent storage in /data/minio..."
mkdir -p /data/minio

echo "[minio-init] MinIO initialization complete"
