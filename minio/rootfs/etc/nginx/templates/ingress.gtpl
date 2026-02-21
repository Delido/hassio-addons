server {
    listen {{ .interface }}:{{ .port }} default_server;

    include /etc/nginx/includes/server_params.conf;
    include /etc/nginx/includes/proxy_params.conf;

    client_max_body_size 0;

    # Allow embedding in Home Assistant
    proxy_hide_header X-Frame-Options;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header Content-Security-Policy "frame-ancestors *";

    location / {
        proxy_pass http://backend/;
        resolver 127.0.0.11 valid=180s;
    }
}

server {
    listen {{ .interface }}:9001 default_server;

    include /etc/nginx/includes/server_params.conf;
    include /etc/nginx/includes/proxy_params.conf;

    client_max_body_size 0;

    location / {
        proxy_pass http://backend/;
        resolver 127.0.0.11 valid=180s;
    }
}
