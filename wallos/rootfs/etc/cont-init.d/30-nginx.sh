#!/command/with-contenv bash
set -e

echo "[init] Configuring nginx reverse proxy..."

# Check if running in Home Assistant
if [ -f /data/options.json ]; then
    # Get addon configuration using jq
    INTERFACE=$(jq -r '.interface // "0.0.0.0"' /data/options.json 2>/dev/null || echo "0.0.0.0")
    PORT=$(jq -r '.ingress_port // 80' /data/options.json 2>/dev/null || echo "80")
else
    INTERFACE="0.0.0.0"
    PORT="80"
fi

echo "[init] Ingress interface: ${INTERFACE}"
echo "[init] Ingress port: ${PORT}"

# Render ingress template using sed (simpler than tempio)
sed -e "s|{{ .interface }}|${INTERFACE}|g" \
    -e "s|{{ .port }}|${PORT}|g" \
    /etc/nginx/templates/ingress.gtpl > /etc/nginx/servers/ingress.conf

echo "[init] Nginx configuration generated successfully"
