#!/usr/bin/with-contenv bashio
set -e

bashio::log.info "Configuring nginx reverse proxy..."

# Get addon configuration
declare interface
declare port
interface=$(bashio::addon.ip_address)
port=$(bashio::addon.ingress_port)

bashio::log.info "Ingress interface: ${interface}"
bashio::log.info "Ingress port: ${port}"

# Render ingress template
bashio::var.json \
    interface "${interface}" \
    port "^${port}" \
    | tempio \
        -template /etc/nginx/templates/ingress.gtpl \
        -out /etc/nginx/servers/ingress.conf

bashio::log.info "Nginx configuration generated successfully"
