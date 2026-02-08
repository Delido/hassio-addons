FROM php:8.3-fpm-alpine

WORKDIR /var/www/html

# Update packages and install dependencies
RUN apk upgrade --no-cache && \
    apk add --no-cache \
    dumb-init \
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

# Clone Wallos from GitHub
RUN git clone --depth 1 https://github.com/ellite/Wallos.git /tmp/wallos && \
    cp -r /tmp/wallos/* /var/www/html/ && \
    rm -rf /tmp/wallos

# Copy Nginx configuration
COPY --from=0 /var/www/html/nginx.conf /etc/nginx/nginx.conf 2>/dev/null || \
    echo "events { worker_connections 1024; } http { include /etc/nginx/mime.types; default_type application/octet-stream; sendfile on; keepalive_timeout 65; server { listen 80; root /var/www/html; index index.php index.html; location / { try_files \$uri \$uri/ /index.php?\$query_string; } location ~ \.php\$ { fastcgi_pass 127.0.0.1:9000; fastcgi_index index.php; include fastcgi_params; fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name; } } }" > /etc/nginx/nginx.conf

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

# Copy HA addon startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 80

ENTRYPOINT ["dumb-init", "--"]
CMD ["/run.sh"]
