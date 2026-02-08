ARG BUILD_FROM=bellamy/wallos:latest
FROM ${BUILD_FROM}

# Install jq for reading HA options.json
RUN apk add --no-cache jq

# Copy HA addon startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
