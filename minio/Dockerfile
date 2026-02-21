# Stage 1: Get minio binary from official image
FROM minio/minio:latest AS minio-source

# Stage 2: Alpine-based runtime with s6-overlay and nginx
FROM alpine:3.19

WORKDIR /data

# Install s6-overlay for service management
ARG S6_OVERLAY_VERSION=3.1.5.0
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz && \
    rm -f /tmp/s6-overlay-*.tar.xz

# Install dependencies
RUN apk upgrade --no-cache && \
    apk add --no-cache \
    bash \
    nginx \
    jq \
    netcat-openbsd \
    tzdata \
    ca-certificates

# Copy minio binary from official image
COPY --from=minio-source /usr/bin/minio /usr/bin/minio

# Backup nginx mime.types, remove default config, set up our structure
RUN mkdir -p /tmp/nginx-backup && \
    cp /etc/nginx/mime.types /tmp/nginx-backup/ 2>/dev/null || true && \
    rm -rf /etc/nginx && \
    mkdir -p /etc/nginx/servers /etc/nginx/includes /etc/nginx/templates

# Copy nginx configs
COPY rootfs/etc/nginx /etc/nginx

# Restore mime.types
RUN cp /tmp/nginx-backup/mime.types /etc/nginx/ && \
    cp /tmp/nginx-backup/mime.types /etc/ && \
    rm -rf /tmp/nginx-backup

# Copy init and service scripts
COPY rootfs/etc/cont-init.d /etc/cont-init.d
COPY rootfs/etc/services.d /etc/services.d

# Fix line endings and make scripts executable
RUN find /etc/cont-init.d/ -type f -exec sed -i 's/\r$//' {} \; && \
    find /etc/services.d/ -type f -exec sed -i 's/\r$//' {} \; && \
    chmod +x /etc/cont-init.d/*.sh && \
    chmod +x /etc/services.d/*/run

# Create data directories
RUN mkdir -p /data/minio

EXPOSE 9000 9001

ENTRYPOINT ["/init"]
