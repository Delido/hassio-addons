# Bitwarden Lite - Home Assistant Add-on

[Bitwarden](https://bitwarden.com) is an open-source password manager. This add-on runs the official **Bitwarden Lite** (unified) deployment - the whole server stack in a single container, designed for small self-hosted installations.

> **Beta:** Bitwarden classes the Lite deployment as beta. It is a password manager holding your most sensitive data - take backups and do not enable automatic add-on updates.

## Before you install

Bitwarden has two hard requirements that are **not** optional:

1. **A free installation ID and key** from <https://bitwarden.com/host/>. The server refuses to start without them.
2. **HTTPS via a real domain.** The web vault uses the browser WebCrypto API, which only works in a secure context. Over plain HTTP the vault loads but you cannot log in or decrypt anything - except on `http://localhost`.

This add-on therefore does **not** use the Home Assistant sidebar (ingress). Bitwarden builds absolute URLs from your domain, and the browser extensions and mobile apps need that same public URL to sync.

## Installation

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the three-dot menu (⋮) → **Repositories**
3. Add this repository URL: `https://github.com/Delido/hassio-addons`
4. Click **Add**
5. Find **Bitwarden Lite** in the store and install it
6. Fill in `domain`, `installation_id` and `installation_key`
7. Start the add-on, then open `https://your-domain/`

The first account you register becomes a regular user. To reach the admin portal at `/admin`, add your address to `admin_emails`.

## Configuration

| Option | Default | Description |
| ------ | ------- | ----------- |
| `domain` | *(required)* | Public URL of your vault, e.g. `https://bitwarden.example.com` |
| `installation_id` | *(required)* | From <https://bitwarden.com/host/> |
| `installation_key` | *(required)* | From <https://bitwarden.com/host/> |
| `timezone` | `Europe/Berlin` | Timezone (e.g. `America/New_York`) |
| `admin_emails` | *(unset)* | Comma-separated addresses allowed into `/admin` |
| `disable_user_registration` | `false` | Block new sign-ups once your accounts exist |
| `hibp_api_key` | *(unset)* | Have I Been Pwned API key for breach reports |
| `database.provider` | `sqlite` | `sqlite`, `mysql`, `postgresql` or `sqlserver` |
| `ssl.enabled` | `false` | Terminate TLS inside the add-on instead of in a proxy |
| `services.*` | see below | Toggle optional Bitwarden services |
| `smtp.*` | *(unset)* | Mail server for invites and password hints |

See [DOCS.md](DOCS.md) for every option in detail.

## Reaching it over HTTPS

**Recommended - reverse proxy.** Leave `ssl.enabled: false`, keep port `8080` published, and point your existing proxy (NGINX Proxy Manager, Caddy, Traefik, the HA *Nginx Proxy Manager* add-on) at `http://<ha-ip>:8080`. The proxy handles the certificate.

**Alternative - TLS in the add-on.** Set `ssl.enabled: true` and publish port `8443`. Certificates are read from Home Assistant's `/ssl` directory, so this pairs with the *Let's Encrypt* or *DuckDNS* add-ons:

```yaml
ssl:
  enabled: true
  certfile: fullchain.pem
  keyfile: privkey.pem
```

If those files are missing, a self-signed certificate is generated - the vault will work, but browsers and mobile apps will warn.

## Ports

| Port | Description |
| ---- | ----------- |
| `8080` | HTTP - point your TLS reverse proxy here |
| `8443` | HTTPS - only when `ssl.enabled` is `true` (disabled by default) |

## Data and backups

Everything lives in `/data/bitwarden` inside the add-on: the SQLite vault, attachments, the data-protection keys and the identity certificate. It is included in Home Assistant backups.

> The `data-protection` directory and `identity.pfx` are as critical as the database. Restoring a database without them leaves accounts unusable - always restore a full add-on backup, never just the `.db` file.

## Resources

Bitwarden Lite needs roughly **1 GB of RAM**. Bitwarden's stated 200 MB minimum applies to a trimmed-down service set. On a Raspberry Pi, disable `icons` and `notifications` if memory is tight.

## Links

- [Bitwarden Lite documentation](https://bitwarden.com/help/install-and-deploy-lite/)
- [Get an installation ID and key](https://bitwarden.com/host/)
- [Upstream source](https://github.com/bitwarden/self-host)
