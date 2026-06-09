# RomDex prototype

A minimal Tkinter application to get started with Python GUI development.

## Run

```bash
python main.py
```

## Features

- Basic window with title and size
- Entry field and buttons
- Menu with About and Help
- Message dialogs

## Notes

Tkinter is included with standard Python installations on Windows, macOS, and many Linux distributions.

## Database (SQLite)

This project uses SQLite via SQLAlchemy. To set up the environment and create the database file:

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app once; the SQLite file will be created at `data/romdex.db` and the `games` table will be created automatically.

