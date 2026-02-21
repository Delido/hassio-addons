# MinIO - Home Assistant Add-on

[MinIO](https://min.io) is a high-performance, S3-compatible object storage server. Use it to store files, backups, and media accessible from Home Assistant and other services on your network.

## Installation

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the three-dot menu (⋮) → **Repositories**
3. Add this repository URL: `https://github.com/Delido/hassio-addons`
4. Click **Add**
5. Find **MinIO** in the store and install it
6. Configure username and password before starting
7. Start the add-on – MinIO Console appears in the sidebar

## Configuration

| Option | Default | Description |
| ------ | ------- | ----------- |
| `timezone` | `Europe/Berlin` | Timezone (e.g. `America/New_York`, `Asia/Tokyo`) |
| `username` | `minioadmin` | MinIO root user / S3 access key |
| `password` | `minioadmin` | MinIO root password / S3 secret key |

> **Note:** Change `username` and `password` before first start. Credentials cannot be changed after the data directory is initialized without resetting the storage.

## Ports

| Port | Description |
| ---- | ----------- |
| `9001` | MinIO Console – web UI (direct external access) |
| `9000` | MinIO API – S3-compatible endpoint |

Ingress is enabled by default – the MinIO Console is accessible directly from the Home Assistant sidebar without exposing port 9001.

## S3 API Access

Other services can connect to MinIO via the S3 API:

- **Endpoint:** `http://<your-ha-ip>:9000`
- **Access Key:** value of `username`
- **Secret Key:** value of `password`
- **Region:** `us-east-1` (or any string – MinIO ignores it)

## Persistent Data

All object data is stored in `/share/minio` and survives add-on updates, restarts, and reinstalls.

## License

This add-on is licensed under the [MIT License](../LICENSE).

Based on [MinIO](https://github.com/minio/minio) by MinIO, Inc. – licensed under [AGPL-3.0](https://github.com/minio/minio/blob/master/LICENSE).
