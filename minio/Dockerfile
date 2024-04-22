# Verwende das MinIO-Image als Basis
FROM minio/minio:latest

# Setze Umgebungsvariablen für Zugriffsschlüssel
ENV MINIO_ACCESS_KEY your_access_key
ENV MINIO_SECRET_KEY your_secret_key
ENV MINIO_ROOT_USER="minioadmin"
ENV MINIO_ROOT_PASSWORD="minioadmin"
ENV MINIO_BROWSER_REDIRECT_URL=""

COPY minio_config.json /root/.minio/config.json

EXPOSE 9000
# Führe den MinIO-Server beim Start des Containers aus
CMD ["server", "/data", "--console-address", ":9001"]
