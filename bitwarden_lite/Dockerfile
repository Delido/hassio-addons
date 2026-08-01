# Pinned deliberately: Bitwarden Lite is beta and this add-on holds a password
# vault, so upstream versions are adopted explicitly rather than by :latest.
FROM ghcr.io/bitwarden/lite:2025.11.1

# The upstream image already ships nginx + supervisord and does all of its
# setup in /entrypoint.sh. We only need jq to translate the Home Assistant
# add-on options into the environment variables that entrypoint expects.
RUN apk add --no-cache jq bash

COPY rootfs/ /

# Only touch our own script - /usr/local/bin/hbs is an upstream binary that
# sed would corrupt.
RUN sed -i 's/\r$//' /usr/local/bin/ha-entrypoint.sh && \
    chmod +x /usr/local/bin/ha-entrypoint.sh

EXPOSE 8080 8443

ENTRYPOINT ["/usr/local/bin/ha-entrypoint.sh"]
