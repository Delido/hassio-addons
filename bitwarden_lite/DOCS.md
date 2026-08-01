# Bitwarden Lite Add-on Documentation

## Options

### `domain`

**Required.** The URL your vault is reached at, e.g. `https://bitwarden.example.com`. A bare hostname also works and is treated as `https://`.

This value ends up in the links of every invite and password-reset mail, and it is what the browser extensions and mobile clients sync against. Changing it later means re-pointing every client, so settle on the final domain before you create accounts.

### `installation_id` / `installation_key`

**Required.** Request a free pair at <https://bitwarden.com/host/>; it arrives by email. The server exits at startup without them.

They identify your instance to Bitwarden's push relay, which is how mobile clients receive sync notifications. They are not a licence and cost nothing.

### `timezone`

**Default:** `Europe/Berlin`

Standard tz database name, e.g. `America/New_York`, `Europe/London`, `Asia/Tokyo`. Affects log timestamps and scheduled jobs.

### `admin_emails`

**Default:** unset

Comma-separated list of email addresses permitted to use the admin portal at `https://your-domain/admin`, e.g. `me@example.com,partner@example.com`.

The admin portal is where you promote users to premium, inspect organisations and delete accounts. Access works by emailed login link, so this only becomes usable once `smtp` is configured. The addresses must correspond to accounts that have registered.

### `disable_user_registration`

**Default:** `false`

When `true`, the sign-up form is rejected. Register your own accounts first, then set this to `true` so an exposed instance cannot collect strangers' accounts. New users can still be added by organisation invite.

### `hibp_api_key`

**Default:** unset

API key from <https://haveibeenpwned.com/API/Key> (paid). Enables the "data breach report" feature. Everything else works without it.

## Database

### `database.provider`

**Default:** `sqlite`

One of `sqlite`, `mysql`, `postgresql`, `sqlserver`.

`sqlite` is the right choice for a household instance: no extra container, and the vault file sits in `/data/bitwarden/vault.db` where Home Assistant backs it up. The other providers exist for larger deployments and require an external server - Bitwarden notes that non-MSSQL providers may perform poorly while Lite is in beta.

### `database.server`, `port`, `database`, `username`, `password`

Only read when `provider` is **not** `sqlite`; `server` is then required. `port` defaults per provider (MySQL 3306, PostgreSQL 5432, SQL Server 1433) and `database` defaults to `bitwarden`.

The database must already exist and the user must own it - Bitwarden creates its own schema on first start but will not create the database itself.

```yaml
database:
  provider: postgresql
  server: 192.168.1.50
  database: bitwarden
  username: bitwarden
  password: your-password
```

## SSL

### `ssl.enabled`

**Default:** `false`

Leave this off if a reverse proxy already terminates TLS - that is the usual Home Assistant setup and avoids a double TLS hop. Turn it on to have the add-on serve HTTPS itself on port `8443`, which you then need to publish.

### `ssl.certfile` / `ssl.keyfile`

**Defaults:** `fullchain.pem` / `privkey.pem`

File names inside Home Assistant's `/ssl` directory, which this add-on mounts read-only. These defaults match what the *Let's Encrypt* and *DuckDNS* add-ons produce, so in most cases you only set `ssl.enabled: true`.

If the files are missing at startup, the add-on logs a warning and the upstream entrypoint generates a self-signed certificate for your domain. The vault works, but clients warn on every connection and some mobile versions refuse to sync at all.

## Services

Each toggle maps to a Bitwarden service. Admin, API and Identity are always on - the vault cannot function without them.

### `services.icons`

**Default:** `true`

Fetches website favicons for vault entries. Purely cosmetic; disabling saves memory and stops outbound requests to `icons.bitwarden.net`.

### `services.notifications`

**Default:** `true`

WebSocket service that pushes live sync to connected clients. With it off, clients still sync, just on their own schedule rather than instantly.

### `services.events`

**Default:** `false`

Audit-log service. Event logs are an organisation/enterprise feature, so leave it off for personal use.

### `services.scim`

**Default:** `false`

Automated user provisioning from an identity provider. Enterprise feature.

### `services.sso`

**Default:** `false`

Login through an external SSO provider. Enterprise feature, and needs additional configuration beyond this add-on.

## SMTP

Optional, but without it Bitwarden cannot send email - which means no organisation invites, no password hints, no email-change confirmations, and **no admin portal access**, since that logs in by emailed link. Vault use itself is unaffected.

Mail is only configured when `smtp.host` is set.

| Option | Default | Description |
| ------ | ------- | ----------- |
| `smtp.host` | unset | Mail server hostname |
| `smtp.port` | `587` | Port |
| `smtp.ssl` | `false` | Implicit TLS - set `true` for port 465 |
| `smtp.starttls` | `true` | STARTTLS - the usual choice for port 587 |
| `smtp.username` | unset | Login user |
| `smtp.password` | unset | Login password |
| `smtp.from` | unset | Sender address; many providers require it to match the account |
| `smtp.trust_server` | `false` | Accept self-signed certificates on the mail server |

Gmail example (needs an [app password](https://support.google.com/accounts/answer/185833)):

```yaml
smtp:
  host: smtp.gmail.com
  port: 587
  starttls: true
  username: you@gmail.com
  password: your-app-password
  from: you@gmail.com
```

## Data storage

All state lives under `/data/bitwarden`, which Home Assistant includes in add-on backups:

| Path | Contents |
| ---- | -------- |
| `vault.db` | The SQLite vault (when `provider` is `sqlite`) |
| `data-protection/` | Keys protecting tokens and secrets at rest |
| `identity.pfx` | Certificate signing authentication tokens |
| `attachments/` | File attachments and Sends |
| `logs/` | Service logs |

`data-protection/` and `identity.pfx` are generated once, on first start, and are as important as the database itself. A database restored without its matching keys leaves every account unable to log in. Always restore a complete add-on backup rather than copying the `.db` file alone.

## Troubleshooting

**Add-on stops right after starting.** Check the log. Missing `domain`, `installation_id` or `installation_key` is reported explicitly and exits.

**Vault loads but login fails, or the page reports crypto errors.** You are on plain HTTP. WebCrypto needs a secure context - put it behind HTTPS.

**Mobile app or extension will not connect.** Usually a self-signed certificate. Use a real certificate from Let's Encrypt.

**`/admin` sends no email.** The admin portal authenticates by emailed link, so it needs a working `smtp` block and your address in `admin_emails`.

**Slow or memory-starved on a Pi.** Set `services.icons` and `services.notifications` to `false`. Bitwarden's 200 MB figure assumes a minimal service set; a full stack wants about 1 GB.

## Updating

The add-on pins a specific upstream Bitwarden version, so updates arrive through add-on updates rather than silently. Take a backup first - Bitwarden advises against automatic upgrades while Lite is in beta.
