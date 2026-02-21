# Wallos - Home Assistant Add-on

Self-hosted subscription and payment tracker with Home Assistant sidebar integration.

## Installation

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the three-dot menu (⋮) → **Repositories**
3. Add this repository URL: `https://github.com/Delido/hassio-addons`
4. Click **Add**
5. Find **Wallos** in the store and install it
6. Start the add-on – Wallos appears automatically in the sidebar

## Configuration

| Option | Default | Description |
| ------ | ------- | ----------- |
| `TZ` | `Europe/Berlin` | Timezone (e.g. `America/New_York`, `Asia/Tokyo`) |

## Ports

| Port | Description |
| ---- | ----------- |
| `3423` | Web interface (direct external access) |

Ingress is enabled by default – Wallos is accessible directly from the Home Assistant sidebar without exposing any port.

## Persistent Data

Data is stored in Home Assistant's `/share/wallos` directory and survives add-on updates, restarts, and reinstalls:

| Path | Contents |
| ---- | -------- |
| `/share/wallos/db` | SQLite database with all subscription data |
| `/share/wallos/logos` | Uploaded subscription logos |

## License

This add-on is licensed under the [MIT License](../LICENSE).

Based on [Wallos](https://github.com/ellite/Wallos) by ellite – licensed under [GPL-3.0](https://github.com/ellite/Wallos/blob/main/LICENSE).
