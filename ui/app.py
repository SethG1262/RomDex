import tkinter as tk
from tkinter import messagebox, ttk

from ui.cloud_library_frame import CloudLibraryFrame
from ui.discovery_frame import DiscoveryFrame
from ui.library_frame import LibraryFrame


class App(tk.Tk):
    """
    Main RomDex application window.

    App is responsible only for the top-level window, navigation,
    shared callbacks, menus, and application shutdown.
    """

    def __init__(self):
        super().__init__()

        self.title("RomDex")
        self.geometry("1150x750")
        self.minsize(1000, 650)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_tabs()
        self._create_menu()

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.library_tab = LibraryFrame(
            self.notebook,
            on_discover_requested=self._show_discovery_tab,
            on_quit_requested=self._on_close
        )

        self.discovery_tab = DiscoveryFrame(self.notebook)

        self.cloud_library_tab = CloudLibraryFrame(
            self.notebook,
            on_library_changed=self.library_tab.refresh_library
        )

        self.notebook.add(
            self.library_tab,
            text="Library"
        )
        self.notebook.add(
            self.discovery_tab,
            text="Discover IGDB"
        )
        self.notebook.add(
            self.cloud_library_tab,
            text="Cloud Library"
        )

        self.notebook.bind(
            "<<NotebookTabChanged>>",
            self._on_tab_changed
        )

    def _create_menu(self):
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(
            menu_bar,
            tearoff=0
        )
        file_menu.add_command(
            label="Add Game",
            command=self.library_tab.add_game
        )
        file_menu.add_command(
            label="Discover IGDB",
            command=self._show_discovery_tab
        )
        file_menu.add_command(
            label="Cloud Library",
            command=self._show_cloud_tab
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self._on_close
        )

        menu_bar.add_cascade(
            label="File",
            menu=file_menu
        )

        help_menu = tk.Menu(
            menu_bar,
            tearoff=0
        )
        help_menu.add_command(
            label="About",
            command=self._show_about
        )
        help_menu.add_command(
            label="Help",
            command=self._show_help
        )

        menu_bar.add_cascade(
            label="Help",
            menu=help_menu
        )

        self.config(menu=menu_bar)

    def _show_discovery_tab(self):
        self.notebook.select(
            self.discovery_tab
        )

    def _show_cloud_tab(self):
        self.notebook.select(
            self.cloud_library_tab
        )

    def _on_tab_changed(self, event):
        selected_tab = self.notebook.select()

        if selected_tab == str(self.library_tab):
            self.library_tab.refresh_library()

        elif selected_tab == str(
            self.cloud_library_tab
        ):
            self.cloud_library_tab.refresh_status()

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "RomDex\n"
            "A privacy-focused Nintendo DS, DSi, "
            "and 3DS library manager."
        )

    def _show_help(self):
        messagebox.showinfo(
            "Help",
            "Library: manage local and saved games.\n"
            "Discover IGDB: search game metadata.\n"
            "Cloud Library: sync metadata and import shared libraries."
        )

    def _on_close(self):
        try:
            self.library_tab.close()
        except Exception:
            pass

        try:
            self.discovery_tab.close()
        except Exception:
            pass

        self.destroy()
