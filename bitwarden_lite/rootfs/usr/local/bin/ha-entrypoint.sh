#!/bin/bash
# Home Assistant add-on wrapper around the upstream Bitwarden Lite entrypoint.
#
# Reads /data/options.json, translates the add-on options into the BW_* /
# globalSettings__* environment variables that /entrypoint.sh consumes, points
# the Bitwarden data directory at /data (so it is covered by HA backups) and
# then hands over to the original entrypoint.
set -e

OPTIONS=/data/options.json
BW_DATA=/data/bitwarden

log() { echo "[bitwarden-lite] $*"; }

opt() {
    # opt <jq-path> <default>
    local value
    if [ -f "${OPTIONS}" ]; then
        value=$(jq -r "${1} // empty" "${OPTIONS}" 2>/dev/null || true)
    fi
    if [ -z "${value}" ] || [ "${value}" = "null" ]; then
        echo "${2}"
    else
        echo "${value}"
    fi
}

# Export an env var only when the value is non-empty, so that we never override
# an upstream default with an empty string.
export_if_set() {
    if [ -n "${2}" ]; then
        export "${1}=${2}"
    fi
}

# --- persistent storage -----------------------------------------------------
# Everything Bitwarden persists has to live under /data, which is the only path
# Home Assistant backs up. The upstream image declares VOLUME ["/etc/bitwarden"],
# so that path is an active mount point: it can be neither removed nor replaced
# by a symlink ("Resource busy").
#
# Instead we bind-mount /data/bitwarden over it. The paths the image exposes as
# environment variables are also redirected, so that even without CAP_SYS_ADMIN
# (i.e. when the bind mount is not permitted) the database, attachments and
# data-protection keys still land in /data.
mkdir -p \
    "${BW_DATA}/attachments/send" \
    "${BW_DATA}/data-protection" \
    "${BW_DATA}/licenses" \
    "${BW_DATA}/logs"

if mount --bind "${BW_DATA}" /etc/bitwarden 2>/dev/null; then
    BW_BIND_MOUNTED=1
    log "Data directory: ${BW_DATA} (bind-mounted to /etc/bitwarden)"
else
    BW_BIND_MOUNTED=0
    log "Data directory: ${BW_DATA} (bind mount unavailable, redirecting paths)"
fi

# Redirect the overridable paths. Harmless when the bind mount succeeded, since
# both paths then refer to the same directory.
export BW_DB_FILE="${BW_DATA}/vault.db"
export globalSettings__dataProtection__directory="${BW_DATA}/data-protection"
export globalSettings__attachment__baseDirectory="${BW_DATA}/attachments"
export globalSettings__send__baseDirectory="${BW_DATA}/attachments/send"
export globalSettings__licenseDirectory="${BW_DATA}/licenses"

# identity.pfx signs the authentication tokens and is hardcoded to
# /etc/bitwarden in the upstream entrypoint - it cannot be redirected. Losing it
# locks every user out, so when the bind mount is unavailable we seed it from
# /data before the entrypoint runs and copy it back afterwards.
if [ "${BW_BIND_MOUNTED}" = "0" ] && [ -f "${BW_DATA}/identity.pfx" ]; then
    cp -f "${BW_DATA}/identity.pfx" /etc/bitwarden/identity.pfx
    log "Restored identity.pfx from ${BW_DATA}"
fi

# --- timezone ---------------------------------------------------------------
TIMEZONE=$(opt '.timezone' 'Europe/Berlin')
if [ -f "/usr/share/zoneinfo/${TIMEZONE}" ]; then
    ln -sf "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime
    echo "${TIMEZONE}" > /etc/timezone
    export TZ="${TIMEZONE}"
    log "Timezone set to ${TIMEZONE}"
fi

# --- core settings ----------------------------------------------------------
DOMAIN=$(opt '.domain' '')
INSTALLATION_ID=$(opt '.installation_id' '')
INSTALLATION_KEY=$(opt '.installation_key' '')

if [ -z "${DOMAIN}" ]; then
    log "ERROR: 'domain' is not configured."
    log "       Set it to the URL your vault is reached at, e.g."
    log "       https://bitwarden.example.com  (https is required by Bitwarden)"
    exit 1
fi

# Bitwarden expects a bare hostname in BW_DOMAIN and builds https://<domain>
# from it, but users tend to paste a full URL. Accept both, and keep the full
# URL for baseServiceUri so http:// setups keep working.
DOMAIN_HOST=${DOMAIN#http://}
DOMAIN_HOST=${DOMAIN_HOST#https://}
DOMAIN_HOST=${DOMAIN_HOST%%/*}
case "${DOMAIN}" in
    http://*|https://*) VAULT_URI="${DOMAIN%/}" ;;
    *)                  VAULT_URI="https://${DOMAIN_HOST}" ;;
esac

export BW_DOMAIN="${DOMAIN_HOST}"
export globalSettings__baseServiceUri__vault="${VAULT_URI}"
log "Vault URL: ${VAULT_URI}"

if [ -z "${INSTALLATION_ID}" ] || [ -z "${INSTALLATION_KEY}" ]; then
    log "ERROR: 'installation_id' and 'installation_key' are required."
    log "       Request a free pair at https://bitwarden.com/host/"
    exit 1
fi
export BW_INSTALLATION_ID="${INSTALLATION_ID}"
export BW_INSTALLATION_KEY="${INSTALLATION_KEY}"

# --- database ---------------------------------------------------------------
DB_PROVIDER=$(opt '.database.provider' 'sqlite')
export BW_DB_PROVIDER="${DB_PROVIDER}"

if [ "${DB_PROVIDER}" = "sqlite" ]; then
    export BW_DB_FILE="${BW_DATA}/vault.db"
    log "Database: sqlite (${BW_DB_FILE})"
else
    export_if_set BW_DB_SERVER   "$(opt '.database.server' '')"
    export_if_set BW_DB_PORT     "$(opt '.database.port' '')"
    export_if_set BW_DB_DATABASE "$(opt '.database.database' 'bitwarden')"
    export_if_set BW_DB_USERNAME "$(opt '.database.username' '')"
    export_if_set BW_DB_PASSWORD "$(opt '.database.password' '')"

    if [ -z "${BW_DB_SERVER}" ]; then
        log "ERROR: database.provider is '${DB_PROVIDER}' but database.server is empty."
        exit 1
    fi
    log "Database: ${DB_PROVIDER} on ${BW_DB_SERVER}"
fi

# --- SSL --------------------------------------------------------------------
# Off by default: the typical HA setup terminates TLS in a reverse proxy
# (NGINX Proxy Manager / Caddy / HA's own duckdns+nginx add-on).
ENABLE_SSL=$(opt '.ssl.enabled' 'false')
export BW_ENABLE_SSL="${ENABLE_SSL}"
if [ "${ENABLE_SSL}" = "true" ]; then
    CERTFILE=$(opt '.ssl.certfile' 'fullchain.pem')
    KEYFILE=$(opt '.ssl.keyfile' 'privkey.pem')
    # HA keeps certificates in /ssl; the entrypoint looks inside /etc/bitwarden.
    if [ -f "/ssl/${CERTFILE}" ] && [ -f "/ssl/${KEYFILE}" ]; then
        cp "/ssl/${CERTFILE}" "${BW_DATA}/ssl.crt"
        cp "/ssl/${KEYFILE}" "${BW_DATA}/ssl.key"
        log "Using certificate /ssl/${CERTFILE}"
    else
        log "WARNING: /ssl/${CERTFILE} or /ssl/${KEYFILE} not found."
        log "         A self-signed certificate will be generated instead."
    fi
    export BW_SSL_CERT="ssl.crt"
    export BW_SSL_KEY="ssl.key"
fi

# --- optional services ------------------------------------------------------
export BW_ENABLE_ADMIN=true
export BW_ENABLE_API=true
export BW_ENABLE_IDENTITY=true
export BW_ENABLE_EVENTS="$(opt '.services.events' 'false')"
export BW_ENABLE_ICONS="$(opt '.services.icons' 'true')"
export BW_ENABLE_NOTIFICATIONS="$(opt '.services.notifications' 'true')"
export BW_ENABLE_SCIM="$(opt '.services.scim' 'false')"
export BW_ENABLE_SSO="$(opt '.services.sso' 'false')"

# --- admin portal / registration -------------------------------------------
export_if_set adminSettings__admins "$(opt '.admin_emails' '')"

DISABLE_REG=$(opt '.disable_user_registration' 'false')
export globalSettings__disableUserRegistration="${DISABLE_REG}"

export_if_set globalSettings__hibpApiKey "$(opt '.hibp_api_key' '')"

# --- SMTP -------------------------------------------------------------------
SMTP_HOST=$(opt '.smtp.host' '')
if [ -n "${SMTP_HOST}" ]; then
    export globalSettings__mail__smtp__host="${SMTP_HOST}"
    export globalSettings__mail__smtp__port="$(opt '.smtp.port' '587')"
    export globalSettings__mail__smtp__ssl="$(opt '.smtp.ssl' 'false')"
    export globalSettings__mail__smtp__startTls="$(opt '.smtp.starttls' 'true')"
    export_if_set globalSettings__mail__smtp__username "$(opt '.smtp.username' '')"
    export_if_set globalSettings__mail__smtp__password "$(opt '.smtp.password' '')"
    export_if_set globalSettings__mail__replyToEmail   "$(opt '.smtp.from' '')"
    export globalSettings__mail__smtp__trustServer="$(opt '.smtp.trust_server' 'false')"
    log "SMTP configured: ${SMTP_HOST}"
else
    log "No SMTP configured - invites and password hints will not be delivered."
fi

# --- hand over to upstream --------------------------------------------------
# The add-on container runs as root and there is no user namespacing to worry
# about, so let the upstream entrypoint keep its own root-owned defaults.
export PUID="${PUID:-0}"
export PGID="${PGID:-0}"

# Without the bind mount, identity.pfx is generated inside the anonymous volume
# and would be lost on the next add-on update. Watch for it in the background
# and copy it into /data once the entrypoint has created it.
if [ "${BW_BIND_MOUNTED}" = "0" ]; then
    (
        i=0
        while [ "${i}" -lt 60 ]; do
            if [ -f /etc/bitwarden/identity.pfx ]; then
                if ! cmp -s /etc/bitwarden/identity.pfx "${BW_DATA}/identity.pfx" 2>/dev/null; then
                    cp -f /etc/bitwarden/identity.pfx "${BW_DATA}/identity.pfx"
                    log "Saved identity.pfx to ${BW_DATA}"
                fi
                break
            fi
            i=$((i + 1))
            sleep 1
        done
    ) &
fi

log "Starting Bitwarden Lite..."
exec /entrypoint.sh
