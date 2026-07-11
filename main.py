from services.db import init_db
from ui.app import App


def main():
    """Creates the database tables and starts RomDex."""
    init_db()

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
