ARG BUILD_FROM=bellamy/wallos:latest
FROM ${BUILD_FROM}

# Install missing dependencies if not present
RUN apk add --no-cache \
    jq \
    nginx \
    dcron \
    php83 \
    php83-fpm \
    php83-pdo \
    php83-pdo_sqlite \
    php83-sqlite3 \
    php83-gd \
    php83-curl \
    php83-zip \
    php83-intl \
    php83-session \
    php83-dom \
    php83-xml \
    php83-calendar \
    dumb-init \
    curl

# Create symlinks for php commands (Alpine 3.x uses versioned binaries)
RUN if [ ! -e /usr/bin/php ]; then ln -s /usr/bin/php83 /usr/bin/php; fi && \
    if [ ! -e /usr/sbin/php-fpm ]; then ln -s /usr/sbin/php-fpm83 /usr/sbin/php-fpm; fi

# Copy HA addon startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
