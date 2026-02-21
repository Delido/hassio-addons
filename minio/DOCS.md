# MinIO Add-on Documentation

## Options

### `timezone`

**Default:** `Europe/Berlin`

The timezone for the container. Use standard tz database names, e.g. `America/New_York`, `Europe/London`, `Asia/Tokyo`.

### `username`

**Default:** `minioadmin`

The MinIO root user name, also used as the S3 access key. Set this before the first start – it cannot be changed later without resetting `/share/minio`.

### `password`

**Default:** `minioadmin`

The MinIO root password, also used as the S3 secret key. Must be at least 8 characters. Set this before the first start.

## Accessing MinIO

### Console (Web UI)

Available via the Home Assistant sidebar (Ingress) or directly at `http://<ha-ip>:9001`.

### S3 API

Connect any S3-compatible client or service:

| Setting | Value |
| ------- | ----- |
| Endpoint | `http://<ha-ip>:9000` |
| Access Key | your `username` value |
| Secret Key | your `password` value |
| Region | `us-east-1` (or any string) |
| Path-style | enabled |

## Data Storage

All buckets and objects are stored persistently in `/share/minio`.
