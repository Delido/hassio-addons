# Wallos - Home Assistant Addon

Self-hosted subscription and payment tracker with sidebar integration.

## Installation

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the three-dot menu (⋮) → **Repositories**
3. Add this repository URL: `https://github.com/Delido/hassio-addons`
4. Click **Add**
5. Find **Wallos** in the store and install it

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `TZ` | `Europe/Berlin` | Timezone for the application |

## Ports

- **3423** - Web interface (external access)

## Usage

After installation and starting the addon, Wallos appears in the Home Assistant sidebar under the name **Wallos**.

## Persistent Data

The following data is stored persistently in Home Assistant's `/share/wallos` directory:

- **Database** (`/share/wallos/db`) – All subscription data
- **Logos** (`/share/wallos/logos`) – Uploaded subscription logos

Data survives addon updates, restarts, and **reinstalls** (even when uninstalling the addon without checking "Delete app data").

## Source

Based on [Wallos](https://github.com/ellite/Wallos) by ellite.
Docker image: `bellamy/wallos:latest`
