

```bash
python main.py
```

## Features

- Basic window with title and size
- Entry field and buttons
- Menu with About and Help
- Message dialogs
- Nintendo DS-family discovery through IGDB
- Firebase-backed cloud library sharing and synchronization

## Notes

Tkinter is included with standard Python installations on Windows, macOS, and many Linux distributions.

## Database (SQLite)

This project uses SQLite via SQLAlchemy. To set up the environment and create the database file:

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app once; the SQLite file will be created at `data/romdex.db` and the `games` table will be created automatically.

## IGDB security

RomDex calls IGDB through a Firebase HTTPS Function. IGDB credentials and the
Twitch access token stay on the server and are not bundled into the desktop
application. See [the IGDB proxy deployment guide](docs/igdb_proxy_deployment.md)
for the one-time project-owner setup.
