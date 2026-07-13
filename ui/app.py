"""Top-level RomDex window with modern sidebar navigation."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ui.cloud_library_frame import CloudLibraryFrame
from ui.discovery_frame import DiscoveryFrame
from ui.library_frame import LibraryFrame
from ui.navigation_sidebar import NavigationSidebar
from ui.page_header import PageHeader
from ui.theme import Colors, apply_theme, style_legacy_widgets


class App(tk.Tk):
    """Main application shell and navigation coordinator."""

    PAGE_DETAILS = {
        "library": {
            "title": "Your Library",
            "subtitle": (
                "Manage saved metadata, attach local ROMs, "
                "and launch games."
            ),
        },
        "discover": {
            "title": "Discover Games",
            "subtitle": (
                "Search Nintendo DS, DSi, and 3DS metadata "
                "through IGDB."
            ),
        },
        "cloud": {
            "title": "Cloud Library",
            "subtitle": (
                "Synchronize metadata and import read-only "
                "shared libraries."
            ),
        },
    }

    LEGACY_PAGE_TITLES = {
        "library": {
            "DS ROM Library",
        },
        "discover": {
            "Discover Nintendo DS / DSi / 3DS Games",
        },
        "cloud": {
            "Cloud Library",
            (
                "Synchronize library metadata and import "
                "read-only shared libraries."
            ),
        },
    }

    def __init__(self):
        super().__init__()

        self.title("RomDex")
        self.geometry("1320x820")
        self.minsize(1080, 680)
        self.configure(background=Colors.BACKGROUND)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        apply_theme(self)

        self._current_page_key: str | None = None
        self._pages: dict[str, ttk.Frame] = {}

        self._create_shell()
        self._create_pages()
        self._bind_shortcuts()

        self.after_idle(self._finish_visual_setup)
        self.show_page("library")

    # ---------------------------------------------------------
    # Application shell
    # ---------------------------------------------------------

    def _create_shell(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = NavigationSidebar(
            self,
            on_navigate=self.show_page,
            on_add_rom=self._add_rom,
            on_emulator_settings=self._open_emulator_settings,
            on_help=self._show_help,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.main_area = ttk.Frame(self, style="App.TFrame")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.columnconfigure(0, weight=1)
        self.main_area.rowconfigure(1, weight=1)

        self.page_header = PageHeader(self.main_area)
        self.page_header.grid(row=0, column=0, sticky="ew")

        ttk.Separator(self.main_area).grid(
            row=0,
            column=0,
            sticky="sew",
        )

        self.page_host = ttk.Frame(
            self.main_area,
            style="App.TFrame",
        )
        self.page_host.grid(row=1, column=0, sticky="nsew")
        self.page_host.columnconfigure(0, weight=1)
        self.page_host.rowconfigure(0, weight=1)

        footer = ttk.Frame(
            self.main_area,
            style="Footer.TFrame",
            padding=(28, 8, 28, 12),
        )
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        self.footer_status = ttk.Label(
            footer,
            text="Ready",
            style="Muted.TLabel",
        )
        self.footer_status.grid(row=0, column=0, sticky="w")

        ttk.Label(
            footer,
            text="ROM files remain on this device",
            style="Muted.TLabel",
        ).grid(row=0, column=1, sticky="e")

    def _create_pages(self) -> None:
        self.library_tab = LibraryFrame(
            self.page_host,
            on_discover_requested=lambda: self.show_page("discover"),
            on_quit_requested=self._on_close,
        )

        self.discovery_tab = DiscoveryFrame(self.page_host)

        self.cloud_library_tab = CloudLibraryFrame(
            self.page_host,
            on_library_changed=self.library_tab.refresh_library,
        )

        self._pages = {
            "library": self.library_tab,
            "discover": self.discovery_tab,
            "cloud": self.cloud_library_tab,
        }

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def show_page(self, page_key: str) -> None:
        """Raise a page, refresh its context, and update navigation."""

        page = self._pages.get(page_key)
        if page is None:
            return

        page.tkraise()
        self.sidebar.select(page_key)
        self._current_page_key = page_key

        details = self.PAGE_DETAILS[page_key]
        self.page_header.set_page(
            title=details["title"],
            subtitle=details["subtitle"],
            actions=self._get_header_actions(page_key),
        )

        self._refresh_page(page_key)
        self._update_footer(page_key)

        self.after_idle(
            lambda selected_page=page: style_legacy_widgets(
                selected_page
            )
        )

    def _get_header_actions(self, page_key: str):
        if page_key == "library":
            return (
                (
                    "＋ Add ROM",
                    self._add_rom,
                    "Accent.TButton",
                ),
                (
                    "↻ Refresh",
                    self.library_tab.refresh_library,
                    "Secondary.TButton",
                ),
            )

        if page_key == "discover":
            return (
                (
                    "Browse games",
                    self._browse_games,
                    "Accent.TButton",
                ),
                (
                    "Open library",
                    lambda: self.show_page("library"),
                    "Secondary.TButton",
                ),
            )

        return (
            (
                "Sync library",
                self._sync_cloud_library,
                "Accent.TButton",
            ),
            (
                "↻ Refresh",
                self.cloud_library_tab.refresh_status,
                "Secondary.TButton",
            ),
        )

    def _refresh_page(self, page_key: str) -> None:
        try:
            if page_key == "library":
                self.library_tab.refresh_library()
            elif page_key == "cloud":
                self.cloud_library_tab.refresh_status()
        except Exception:
            # The page itself already presents operational errors.
            pass

    def _update_footer(self, page_key: str) -> None:
        statuses = {
            "library": "Library ready",
            "discover": "IGDB discovery • Internet connection required",
            "cloud": "Cloud synchronization uses metadata only",
        }
        self.footer_status.configure(text=statuses[page_key])

    # ---------------------------------------------------------
    # Quick actions
    # ---------------------------------------------------------

    def _add_rom(self) -> None:
        self.show_page("library")
        self.library_tab.add_game()

    def _open_emulator_settings(self) -> None:
        self.library_tab.open_emulator_configuration()

    def _browse_games(self) -> None:
        self.show_page("discover")
        browse_method = getattr(
            self.discovery_tab,
            "_start_browse",
            None,
        )
        if callable(browse_method):
            browse_method()

    def _sync_cloud_library(self) -> None:
        self.show_page("cloud")
        sync_method = getattr(
            self.cloud_library_tab,
            "_sync_library",
            None,
        )
        if callable(sync_method):
            sync_method()

    def _refresh_current_page(self) -> None:
        if self._current_page_key:
            self._refresh_page(self._current_page_key)

    # ---------------------------------------------------------
    # Visual cleanup
    # ---------------------------------------------------------

    def _finish_visual_setup(self) -> None:
        self._hide_legacy_page_headings()
        style_legacy_widgets(self)

    def _hide_legacy_page_headings(self) -> None:
        """Remove old in-page headings now replaced by PageHeader."""

        for page_key, page in self._pages.items():
            hidden_texts = self.LEGACY_PAGE_TITLES[page_key]

            for child in page.winfo_children():
                try:
                    child_text = child.cget("text")
                except (tk.TclError, AttributeError):
                    continue

                if child_text not in hidden_texts:
                    continue

                try:
                    child.pack_forget()
                except tk.TclError:
                    try:
                        child.grid_remove()
                    except tk.TclError:
                        pass

    # ---------------------------------------------------------
    # Keyboard shortcuts
    # ---------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        self.bind_all(
            "<Control-o>",
            lambda event: self._add_rom(),
        )
        self.bind_all(
            "<Control-l>",
            lambda event: self.show_page("library"),
        )
        self.bind_all(
            "<Control-d>",
            lambda event: self.show_page("discover"),
        )
        self.bind_all(
            "<Control-Shift-C>",
            lambda event: self.show_page("cloud"),
        )
        self.bind_all(
            "<Control-comma>",
            lambda event: self._open_emulator_settings(),
        )
        self.bind_all(
            "<F5>",
            lambda event: self._refresh_current_page(),
        )
        self.bind_all(
            "<Control-q>",
            lambda event: self._on_close(),
        )

    # ---------------------------------------------------------
    # Help and shutdown
    # ---------------------------------------------------------

    def _show_help(self) -> None:
        messagebox.showinfo(
            "RomDex Help",
            "Navigation\n"
            "• Library: manage local and saved games.\n"
            "• Discover: search IGDB metadata.\n"
            "• Cloud Library: sync metadata and import shares.\n\n"
            "Keyboard shortcuts\n"
            "• Ctrl+O: Add ROM\n"
            "• Ctrl+L: Open Library\n"
            "• Ctrl+D: Open Discover\n"
            "• Ctrl+Shift+C: Open Cloud Library\n"
            "• Ctrl+,: Emulator settings\n"
            "• F5: Refresh current page\n"
            "• Ctrl+Q: Exit RomDex",
            parent=self,
        )

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About RomDex",
            "RomDex\n\n"
            "A local-first Nintendo DS, DSi, and 3DS "
            "library manager.\n\n"
            "ROM files stay on your computer.",
            parent=self,
        )

    def _on_close(self) -> None:
        try:
            self.library_tab.close()
        except Exception:
            pass

        try:
            self.discovery_tab.close()
        except Exception:
            pass

        self.destroy()
