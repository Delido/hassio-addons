FROM php:8.3-fpm-alpine

WORKDIR /var/www/html

# Install s6-overlay for service management
ARG S6_OVERLAY_VERSION=3.1.5.0
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz && \
    rm -f /tmp/s6-overlay-*.tar.xz

# Update packages and install dependencies
RUN apk upgrade --no-cache && \
    apk add --no-cache \
    bash \
    shadow \
    sqlite-dev \
    libpng libpng-dev \
    libjpeg-turbo libjpeg-turbo-dev \
    freetype freetype-dev \
    curl \
    autoconf \
    libgomp \
    icu-dev icu-data-full \
    nginx \
    dcron \
    tzdata \
    imagemagick imagemagick-dev \
    libzip-dev \
    sqlite \
    libwebp-dev \
    jq \
    git && \
    docker-php-ext-install pdo pdo_sqlite calendar && \
    docker-php-ext-enable pdo pdo_sqlite && \
    docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp && \
    docker-php-ext-install -j$(nproc) gd intl zip && \
    apk add --no-cache --virtual .build-deps $PHPIZE_DEPS && \
    pecl install imagick && \
    docker-php-ext-enable imagick && \
    apk del .build-deps

# Install Home Assistant tools (bashio and tempio)
ARG BASHIO_VERSION=0.16.2
ARG TEMPIO_VERSION=2021.09.0
RUN curl -L -s -o /usr/bin/bashio \
    "https://github.com/hassio-addons/bashio/releases/download/v${BASHIO_VERSION}/bashio" && \
    chmod a+x /usr/bin/bashio && \
    curl -L -s -o /usr/bin/tempio \
    "https://github.com/home-assistant/tempio/releases/download/${TEMPIO_VERSION}/tempio_amd64" && \
    chmod a+x /usr/bin/tempio

# Clone Wallos from GitHub
RUN git clone --depth 1 https://github.com/ellite/Wallos.git /tmp/wallos && \
    cp -r /tmp/wallos/* /var/www/html/ && \
    rm -rf /tmp/wallos

# Patch Wallos nginx.conf to listen on port 8080 instead of 80
RUN if [ -f /var/www/html/nginx.conf ]; then \
        sed -i 's/listen.*80/listen 127.0.0.1:8080/g' /var/www/html/nginx.conf && \
        cp /var/www/html/nginx.conf /etc/wallos-nginx.conf; \
    fi

# Remove default Alpine nginx configs
RUN rm -rf /etc/nginx && mkdir -p /etc/nginx/servers /etc/nginx/includes

# Copy rootfs (nginx reverse proxy configs and init scripts)
COPY rootfs /

# Make init scripts and service scripts executable
RUN chmod +x /etc/cont-init.d/*.sh && \
    chmod +x /etc/services.d/*/run

# Set up cron
RUN if [ -f /var/www/html/cronjobs ]; then \
        dos2unix /var/www/html/cronjobs 2>/dev/null || sed -i 's/\r$//' /var/www/html/cronjobs; \
        chmod 0644 /var/www/html/cronjobs; \
        /usr/bin/crontab /var/www/html/cronjobs; \
    fi && \
    mkdir -p /var/log/cron && \
    chown -R www-data:www-data /var/www/html && \
    echo 'pm.max_children = 15' >> /usr/local/etc/php-fpm.d/zz-docker.conf && \
    echo 'pm.max_requests = 500' >> /usr/local/etc/php-fpm.d/zz-docker.conf

EXPOSE 80

ENTRYPOINT ["/init"]
