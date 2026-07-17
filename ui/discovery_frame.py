"""Modern, responsive IGDB discovery page for RomDex."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from repositories.game_repository import GameRepository
from services.discovery_filter_service import DiscoveryFilterService
from services.igdb_service import IGDBService


try:
    from ui.theme import Colors, Fonts
except ImportError:
    # Fallback palette for projects that have not installed theme.py.
    class Colors:
        BACKGROUND = "#0D1117"
        SURFACE = "#161C25"
        SURFACE_ALT = "#1D2531"
        SURFACE_HOVER = "#263140"
        BORDER = "#2C3746"
        TEXT = "#F4F7FB"
        TEXT_SECONDARY = "#A8B3C2"
        TEXT_MUTED = "#778394"
        ACCENT = "#7C5CFC"
        ACCENT_HOVER = "#8D72FF"
        ACCENT_SOFT = "#282246"
        SUCCESS = "#49C98A"
        WARNING = "#F4BE5B"

    class Fonts:
        FAMILY = "Segoe UI"
        BODY = (FAMILY, 10)
        BODY_BOLD = (FAMILY, 10, "bold")
        SMALL = (FAMILY, 9)
        SMALL_BOLD = (FAMILY, 9, "bold")
        SECTION_TITLE = (FAMILY, 12, "bold")


class DiscoveryFrame(ttk.Frame):
    """Searches, filters, previews, and saves IGDB game metadata."""

    FILTER_DEFAULTS = {
        "title": "",
        "platform": "All Platforms",
        "year": "All Years",
        "genre": "All Genres",
        "cover": "All Games",
        "sort": "Title A-Z",
    }

    FILTER_WIDE_WIDTH = 900
    FILTER_MEDIUM_WIDTH = 620
    CONTENT_WIDE_WIDTH = 900

    def __init__(self, parent):
        self._configure_styles(parent)
        super().__init__(parent, style="DiscoveryPage.TFrame")

        self.igdb_service = IGDBService()
        self.game_repository = GameRepository()
        self.discovery_filter_service = DiscoveryFilterService()

        # Full unfiltered results returned for the current IGDB page.
        self.page_results = []

        # Filtered results currently shown in the table.
        self.results = []

        self.page_size = 50
        self.current_offset = 0
        self.current_page = 1
        self.current_mode = None
        self.current_search_term = ""

        self._filters_expanded = True
        self._filter_column_count = None
        self._content_is_wide = None
        self._resize_job = None
        self._chip_widgets = []
        self._is_loading = False

        self.search_var = tk.StringVar()
        self.filter_title_var = tk.StringVar()
        self.platform_var = tk.StringVar(
            value=self.FILTER_DEFAULTS["platform"]
        )
        self.year_var = tk.StringVar(
            value=self.FILTER_DEFAULTS["year"]
        )
        self.genre_var = tk.StringVar(
            value=self.FILTER_DEFAULTS["genre"]
        )
        self.cover_var = tk.StringVar(
            value=self.FILTER_DEFAULTS["cover"]
        )
        self.sort_var = tk.StringVar(
            value=self.FILTER_DEFAULTS["sort"]
        )

        self._filter_fields = []

        self._create_widgets()
        self.bind("<Configure>", self._schedule_responsive_layout)
        self.after_idle(self._finish_setup)

    # ---------------------------------------------------------
    # Styling
    # ---------------------------------------------------------

    @staticmethod
    def _configure_styles(parent) -> None:
        style = ttk.Style(parent)

        style.configure(
            "DiscoveryPage.TFrame",
            background=Colors.BACKGROUND,
        )
        style.configure(
            "DiscoveryCard.TFrame",
            background=Colors.SURFACE,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BORDER,
            darkcolor=Colors.BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "DiscoverySurface.TFrame",
            background=Colors.SURFACE,
        )
        style.configure(
            "DiscoveryTitle.TLabel",
            background=Colors.SURFACE,
            foreground=Colors.TEXT,
            font=Fonts.SECTION_TITLE,
        )
        style.configure(
            "DiscoverySubtitle.TLabel",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_MUTED,
            font=Fonts.SMALL,
        )
        style.configure(
            "DiscoveryField.TLabel",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_SECONDARY,
            font=Fonts.SMALL_BOLD,
        )
        style.configure(
            "DiscoveryStatus.TLabel",
            background=Colors.BACKGROUND,
            foreground=Colors.TEXT_SECONDARY,
            font=Fonts.SMALL,
        )
        style.configure(
            "DiscoveryPageBadge.TLabel",
            background=Colors.ACCENT_SOFT,
            foreground=Colors.TEXT,
            font=Fonts.SMALL_BOLD,
            padding=(11, 7),
        )
        style.configure(
            "DiscoveryLink.TButton",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_SECONDARY,
            bordercolor=Colors.SURFACE,
            lightcolor=Colors.SURFACE,
            darkcolor=Colors.SURFACE,
            padding=(8, 7),
            font=Fonts.SMALL_BOLD,
            relief="flat",
        )
        style.map(
            "DiscoveryLink.TButton",
            background=[
                ("pressed", Colors.SURFACE_ALT),
                ("active", Colors.SURFACE_ALT),
            ],
            foreground=[
                ("disabled", Colors.TEXT_MUTED),
                ("active", Colors.TEXT),
            ],
        )
        style.configure(
            "DiscoveryToggle.TButton",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_SECONDARY,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.SURFACE,
            darkcolor=Colors.SURFACE,
            padding=(11, 7),
            font=Fonts.SMALL_BOLD,
            relief="flat",
        )
        style.map(
            "DiscoveryToggle.TButton",
            background=[
                ("pressed", Colors.SURFACE_ALT),
                ("active", Colors.SURFACE_HOVER),
            ],
            foreground=[("active", Colors.TEXT)],
            bordercolor=[("active", Colors.ACCENT)],
        )

    # ---------------------------------------------------------
    # Page construction
    # ---------------------------------------------------------

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._create_search_card()
        self._create_filter_card()
        self._create_page_toolbar()
        self._create_content_area()

    def _create_search_card(self) -> None:
        self.search_card = ttk.Frame(
            self,
            style="DiscoveryCard.TFrame",
            padding=(16, 14),
        )
        self.search_card.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(12, 10),
        )
        self.search_card.columnconfigure(0, weight=1)

        text_frame = ttk.Frame(
            self.search_card,
            style="DiscoverySurface.TFrame",
        )
        text_frame.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 11),
        )

        ttk.Label(
            text_frame,
            text="Search the IGDB catalogue",
            style="DiscoveryTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            text_frame,
            text=(
                "Find Nintendo DS, DSi, and 3DS metadata, "
                "then save the games you want."
            ),
            style="DiscoverySubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.search_entry = ttk.Entry(
            self.search_card,
            textvariable=self.search_var,
        )
        self.search_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        self.search_entry.bind(
            "<Return>",
            lambda _event: self._start_search(),
        )

        self.search_button = ttk.Button(
            self.search_card,
            text="⌕  Search",
            style="Accent.TButton",
            command=self._start_search,
        )
        self.search_button.grid(
            row=1,
            column=1,
            padx=(0, 8),
        )

        self.browse_button = ttk.Button(
            self.search_card,
            text="Browse all",
            style="Secondary.TButton",
            command=self._start_browse,
        )
        self.browse_button.grid(
            row=1,
            column=2,
        )

    def _create_filter_card(self) -> None:
        self.filter_card = ttk.Frame(
            self,
            style="DiscoveryCard.TFrame",
            padding=(16, 14),
        )
        self.filter_card.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 10),
        )
        self.filter_card.columnconfigure(0, weight=1)

        header = ttk.Frame(
            self.filter_card,
            style="DiscoverySurface.TFrame",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(
            header,
            style="DiscoverySurface.TFrame",
        )
        title_frame.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            title_frame,
            text="Discovery filters",
            style="DiscoveryTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text=(
                "These filters apply to the games loaded on "
                "the current IGDB page."
            ),
            style="DiscoverySubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.active_filter_badge = tk.Label(
            header,
            text="No filters active",
            background=Colors.SURFACE_ALT,
            foreground=Colors.TEXT_MUTED,
            font=Fonts.SMALL_BOLD,
            padx=10,
            pady=5,
            borderwidth=0,
        )
        self.active_filter_badge.grid(
            row=0,
            column=1,
            padx=(12, 8),
        )

        self.reset_filter_button = ttk.Button(
            header,
            text="Reset",
            style="DiscoveryLink.TButton",
            state="disabled",
            command=self._reset_discovery_filters,
        )
        self.reset_filter_button.grid(
            row=0,
            column=2,
            padx=(0, 5),
        )

        self.filter_toggle_button = ttk.Button(
            header,
            text="Hide  ▴",
            style="DiscoveryToggle.TButton",
            command=self._toggle_filters,
        )
        self.filter_toggle_button.grid(
            row=0,
            column=3,
        )

        self.filter_body = ttk.Frame(
            self.filter_card,
            style="DiscoverySurface.TFrame",
        )
        self.filter_body.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(14, 0),
        )

        self.platform_filter = self._create_filter_combobox(
            "Platform",
            self.platform_var,
            ("All Platforms",),
        )
        self.year_filter = self._create_filter_combobox(
            "Release year",
            self.year_var,
            ("All Years",),
        )
        self.genre_filter = self._create_filter_combobox(
            "Genre",
            self.genre_var,
            ("All Genres",),
        )
        self.cover_filter = self._create_filter_combobox(
            "Cover art",
            self.cover_var,
            ("All Games", "Has Cover", "No Cover"),
        )
        self.sort_filter = self._create_filter_combobox(
            "Sort by",
            self.sort_var,
            (
                "Title A-Z",
                "Title Z-A",
                "Release Year Newest",
                "Release Year Oldest",
            ),
        )

        self.active_filter_row = ttk.Frame(
            self.filter_card,
            style="DiscoverySurface.TFrame",
        )
        self.active_filter_row.columnconfigure(1, weight=1)

        ttk.Label(
            self.active_filter_row,
            text="ACTIVE",
            style="DiscoveryField.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
        )

        self.filter_chip_frame = ttk.Frame(
            self.active_filter_row,
            style="DiscoverySurface.TFrame",
        )
        self.filter_chip_frame.grid(
            row=0,
            column=1,
            sticky="ew",
        )

    def _create_filter_entry(
        self,
        label_text: str,
        variable: tk.StringVar,
    ) -> ttk.Entry:
        frame = self._create_filter_field_frame(label_text)

        entry = ttk.Entry(
            frame,
            textvariable=variable,
        )
        entry.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        entry.bind(
            "<KeyRelease>",
            lambda _event: self._apply_discovery_filters(),
        )

        return entry

    def _create_filter_combobox(
        self,
        label_text: str,
        variable: tk.StringVar,
        values,
    ) -> ttk.Combobox:
        frame = self._create_filter_field_frame(label_text)

        combobox = ttk.Combobox(
            frame,
            textvariable=variable,
            state="readonly",
            values=values,
        )
        combobox.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        combobox.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._apply_discovery_filters(),
        )

        return combobox

    def _create_filter_field_frame(
        self,
        label_text: str,
    ) -> ttk.Frame:
        frame = ttk.Frame(
            self.filter_body,
            style="DiscoverySurface.TFrame",
        )
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text=label_text.upper(),
            style="DiscoveryField.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        self._filter_fields.append(frame)
        return frame

    def _create_page_toolbar(self) -> None:
        self.page_toolbar = ttk.Frame(
            self,
            style="DiscoveryPage.TFrame",
        )
        self.page_toolbar.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 9),
        )
        self.page_toolbar.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            self.page_toolbar,
            text="Search or browse to load games.",
            style="DiscoveryStatus.TLabel",
        )
        self.status_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.previous_button = ttk.Button(
            self.page_toolbar,
            text="← Previous",
            style="Secondary.TButton",
            state="disabled",
            command=self._previous_page,
        )
        self.previous_button.grid(
            row=0,
            column=1,
            padx=(8, 7),
        )

        self.page_label = ttk.Label(
            self.page_toolbar,
            text="Page 1",
            style="DiscoveryPageBadge.TLabel",
        )
        self.page_label.grid(
            row=0,
            column=2,
        )

        self.next_button = ttk.Button(
            self.page_toolbar,
            text="Next →",
            style="Secondary.TButton",
            state="disabled",
            command=self._next_page,
        )
        self.next_button.grid(
            row=0,
            column=3,
            padx=(7, 0),
        )

    def _create_content_area(self) -> None:
        self.content_frame = ttk.Frame(
            self,
            style="DiscoveryPage.TFrame",
        )
        self.content_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 14),
        )

        self.results_card = ttk.Frame(
            self.content_frame,
            style="DiscoveryCard.TFrame",
            padding=(14, 12),
        )
        self.results_card.columnconfigure(0, weight=1)
        self.results_card.rowconfigure(1, weight=1)

        results_header = ttk.Frame(
            self.results_card,
            style="DiscoverySurface.TFrame",
        )
        results_header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 9),
        )
        results_header.columnconfigure(0, weight=1)

        ttk.Label(
            results_header,
            text="Results",
            style="DiscoveryTitle.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.result_count_label = ttk.Label(
            results_header,
            text="0 games",
            style="DiscoverySubtitle.TLabel",
        )
        self.result_count_label.grid(
            row=0,
            column=1,
            sticky="e",
        )

        table_frame = ttk.Frame(
            self.results_card,
            style="DiscoverySurface.TFrame",
        )
        table_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("title", "platform", "release_date")
        self.results_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.results_table.heading("title", text="Title")
        self.results_table.heading("platform", text="Platform")
        self.results_table.heading(
            "release_date",
            text="Release Date",
        )
        self.results_table.column(
            "title",
            width=340,
            minwidth=170,
            stretch=True,
        )
        self.results_table.column(
            "platform",
            width=180,
            minwidth=110,
            stretch=True,
        )
        self.results_table.column(
            "release_date",
            width=120,
            minwidth=95,
            stretch=False,
            anchor="center",
        )

        table_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.results_table.yview,
        )
        self.results_table.configure(
            yscrollcommand=table_scrollbar.set
        )

        self.results_table.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        table_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.results_table.bind(
            "<<TreeviewSelect>>",
            self._on_game_selected,
        )

        self.details_card = ttk.Frame(
            self.content_frame,
            style="DiscoveryCard.TFrame",
            padding=(14, 12),
        )
        self.details_card.columnconfigure(0, weight=1)
        self.details_card.rowconfigure(1, weight=1)

        details_header = ttk.Frame(
            self.details_card,
            style="DiscoverySurface.TFrame",
        )
        details_header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 9),
        )

        ttk.Label(
            details_header,
            text="Game details",
            style="DiscoveryTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            details_header,
            text="Select a result to preview its metadata.",
            style="DiscoverySubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        details_text_frame = ttk.Frame(
            self.details_card,
            style="DiscoverySurface.TFrame",
        )
        details_text_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        details_text_frame.columnconfigure(0, weight=1)
        details_text_frame.rowconfigure(0, weight=1)

        self.details_text = tk.Text(
            details_text_frame,
            width=36,
            height=10,
            wrap="word",
            state="disabled",
            background=Colors.SURFACE_ALT,
            foreground=Colors.TEXT_SECONDARY,
            insertbackground=Colors.TEXT,
            selectbackground=Colors.ACCENT,
            selectforeground="#FFFFFF",
            highlightbackground=Colors.BORDER,
            highlightcolor=Colors.ACCENT,
            highlightthickness=1,
            borderwidth=0,
            relief="flat",
            padx=12,
            pady=10,
            font=Fonts.BODY,
        )

        details_scrollbar = ttk.Scrollbar(
            details_text_frame,
            orient="vertical",
            command=self.details_text.yview,
        )
        self.details_text.configure(
            yscrollcommand=details_scrollbar.set
        )

        self.details_text.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        details_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.save_button = ttk.Button(
            self.details_card,
            text="＋  Save selected to Library",
            style="Accent.TButton",
            state="disabled",
            command=self._save_selected_game,
        )
        self.save_button.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        self._set_details(
            "Search for a game or browse the IGDB catalogue.\n\n"
            "Select a result to view its platform, release date, "
            "genres, summary, and storyline."
        )

    # ---------------------------------------------------------
    # Responsive layout
    # ---------------------------------------------------------

    def _finish_setup(self) -> None:
        self._apply_responsive_layout()
        self._update_filter_state()
        self.search_entry.focus_set()

    def _schedule_responsive_layout(self, _event=None) -> None:
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except tk.TclError:
                pass

        self._resize_job = self.after(
            40,
            self._apply_responsive_layout,
        )

    def _apply_responsive_layout(self) -> None:
        self._resize_job = None
        width = self.winfo_width()

        self._layout_filter_fields(width)
        self._layout_content(width)

    def _layout_filter_fields(self, width: int) -> None:
        if width >= self.FILTER_WIDE_WIDTH:
            column_count = 3
        elif width >= self.FILTER_MEDIUM_WIDTH:
            column_count = 2
        else:
            column_count = 1

        if column_count == self._filter_column_count:
            return

        for index in range(3):
            self.filter_body.columnconfigure(index, weight=0)

        for frame in self._filter_fields:
            frame.grid_forget()

        for index in range(column_count):
            self.filter_body.columnconfigure(
                index,
                weight=1,
                uniform="discovery_filter_columns",
            )

        for index, frame in enumerate(self._filter_fields):
            row = index // column_count
            column = index % column_count

            frame.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(
                    0 if column == 0 else 7,
                    0 if column == column_count - 1 else 7,
                ),
                pady=(
                    0 if row == 0 else 12,
                    0,
                ),
            )

        self._filter_column_count = column_count

    def _layout_content(self, width: int) -> None:
        use_wide_layout = width >= self.CONTENT_WIDE_WIDTH

        if use_wide_layout == self._content_is_wide:
            return

        self.results_card.grid_forget()
        self.details_card.grid_forget()

        for column in range(2):
            self.content_frame.columnconfigure(column, weight=0)

        for row in range(2):
            self.content_frame.rowconfigure(row, weight=0)

        if use_wide_layout:
            self.content_frame.columnconfigure(0, weight=3)
            self.content_frame.columnconfigure(1, weight=2)
            self.content_frame.rowconfigure(0, weight=1)

            self.results_card.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=(0, 8),
            )
            self.details_card.grid(
                row=0,
                column=1,
                sticky="nsew",
                padx=(8, 0),
            )
        else:
            self.content_frame.columnconfigure(0, weight=1)
            self.content_frame.rowconfigure(0, weight=3)
            self.content_frame.rowconfigure(1, weight=2)

            self.results_card.grid(
                row=0,
                column=0,
                sticky="nsew",
                pady=(0, 8),
            )
            self.details_card.grid(
                row=1,
                column=0,
                sticky="nsew",
                pady=(8, 0),
            )

        self._content_is_wide = use_wide_layout

    # ---------------------------------------------------------
    # Search and pagination
    # ---------------------------------------------------------

    def _start_search(self) -> None:
        search_term = self.search_var.get().strip()

        if not search_term:
            messagebox.showwarning(
                "Missing Search",
                "Please enter a game title.",
                parent=self,
            )
            self.search_entry.focus_set()
            return

        self.current_mode = "search"
        self.current_search_term = search_term
        self.current_offset = 0
        self.current_page = 1
        self._load_current_page()

    def _start_browse(self) -> None:
        self.current_mode = "browse"
        self.current_search_term = ""
        self.current_offset = 0
        self.current_page = 1
        self._load_current_page()

    def _next_page(self) -> None:
        if not self.current_mode:
            messagebox.showinfo(
                "No Search",
                "Search or browse first.",
                parent=self,
            )
            return

        self.current_offset += self.page_size
        self.current_page += 1
        self._load_current_page()

    def _previous_page(self) -> None:
        if not self.current_mode:
            messagebox.showinfo(
                "No Search",
                "Search or browse first.",
                parent=self,
            )
            return

        if self.current_offset == 0:
            return

        self.current_offset -= self.page_size
        self.current_page -= 1
        self._load_current_page()

    def _load_current_page(self) -> None:
        try:
            self._set_loading_state(True)

            if self.current_mode == "search":
                games = (
                    self.igdb_service.search_ds_family_games_page(
                        self.current_search_term,
                        limit=self.page_size,
                        offset=self.current_offset,
                    )
                )
            elif self.current_mode == "browse":
                games = self.igdb_service.get_ds_family_games_page(
                    limit=self.page_size,
                    offset=self.current_offset,
                )
            else:
                games = []

            self.page_results = games
            self._refresh_discovery_filter_options()
            self._reset_discovery_filters()

        except Exception as error:
            self.status_label.configure(
                text="The IGDB request could not be completed."
            )
            self._set_details(
                "RomDex could not load this IGDB page.\n\n"
                f"{error}"
            )
            messagebox.showerror(
                "IGDB Error",
                str(error),
                parent=self,
            )
        finally:
            self._set_loading_state(False)
            self._update_pagination_state()

    def _set_loading_state(self, is_loading: bool) -> None:
        self._is_loading = is_loading

        state = "disabled" if is_loading else "normal"
        self.search_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.search_entry.configure(
            state="disabled" if is_loading else "normal"
        )

        if is_loading:
            self._clear_results_table()
            self.result_count_label.configure(text="Loading…")
            self.status_label.configure(
                text="Loading games from IGDB…"
            )
            self._set_details(
                "Loading games from IGDB…\n\n"
                "This can take a moment depending on the network."
            )
            self.save_button.configure(state="disabled")
            self.previous_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            self.update_idletasks()

    def _update_pagination_state(self) -> None:
        if self._is_loading or not self.current_mode:
            self.previous_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            return

        self.previous_button.configure(
            state=(
                "normal"
                if self.current_offset > 0
                else "disabled"
            )
        )

        self.next_button.configure(
            state=(
                "normal"
                if len(self.page_results) == self.page_size
                else "disabled"
            )
        )

    # ---------------------------------------------------------
    # Discovery filters
    # ---------------------------------------------------------

    def _toggle_filters(self) -> None:
        self._filters_expanded = not self._filters_expanded

        if self._filters_expanded:
            self.filter_body.grid()
            self.filter_toggle_button.configure(text="Hide  ▴")
            self._layout_filter_fields(self.winfo_width())

            if self._get_active_filters():
                self.active_filter_row.grid(
                    row=2,
                    column=0,
                    sticky="ew",
                    pady=(12, 0),
                )
        else:
            self.filter_body.grid_remove()
            self.active_filter_row.grid_remove()
            self.filter_toggle_button.configure(text="Show  ▾")

    def _apply_discovery_filters(self) -> None:
        filtered_games = self.discovery_filter_service.filter_games(
            games=self.page_results,
            title=self.filter_title_var.get(),
            platform=self.platform_var.get(),
            release_year=self.year_var.get(),
            genre=self.genre_var.get(),
            cover_option=self.cover_var.get(),
            sort_option=self.sort_var.get(),
        )

        self._update_filter_state()
        self._display_results(filtered_games, filtered=True)

    def _reset_discovery_filters(self) -> None:
        self.filter_title_var.set(self.FILTER_DEFAULTS["title"])
        self.platform_var.set(self.FILTER_DEFAULTS["platform"])
        self.year_var.set(self.FILTER_DEFAULTS["year"])
        self.genre_var.set(self.FILTER_DEFAULTS["genre"])
        self.cover_var.set(self.FILTER_DEFAULTS["cover"])
        self.sort_var.set(self.FILTER_DEFAULTS["sort"])

        self._update_filter_state()

        default_results = self.discovery_filter_service.filter_games(
            games=self.page_results,
            sort_option=self.FILTER_DEFAULTS["sort"],
        )
        self._display_results(default_results, filtered=False)

    def _refresh_discovery_filter_options(self) -> None:
        platform_options = (
            self.discovery_filter_service.get_platform_options(
                self.page_results
            )
        )
        year_options = (
            self.discovery_filter_service.get_year_options(
                self.page_results
            )
        )
        genre_options = (
            self.discovery_filter_service.get_genre_options(
                self.page_results
            )
        )

        self.platform_filter.configure(values=platform_options)
        self.year_filter.configure(values=year_options)
        self.genre_filter.configure(values=genre_options)

        if self.platform_var.get() not in platform_options:
            self.platform_var.set(
                self.FILTER_DEFAULTS["platform"]
            )

        if self.year_var.get() not in year_options:
            self.year_var.set(self.FILTER_DEFAULTS["year"])

        if self.genre_var.get() not in genre_options:
            self.genre_var.set(self.FILTER_DEFAULTS["genre"])

    def _get_active_filters(self):
        values = (
            (
                "title",
                "Title",
                self.filter_title_var.get().strip(),
                self.FILTER_DEFAULTS["title"],
            ),
            (
                "platform",
                "Platform",
                self.platform_var.get(),
                self.FILTER_DEFAULTS["platform"],
            ),
            (
                "year",
                "Year",
                self.year_var.get(),
                self.FILTER_DEFAULTS["year"],
            ),
            (
                "genre",
                "Genre",
                self.genre_var.get(),
                self.FILTER_DEFAULTS["genre"],
            ),
            (
                "cover",
                "Cover",
                self.cover_var.get(),
                self.FILTER_DEFAULTS["cover"],
            ),
            (
                "sort",
                "Sort",
                self.sort_var.get(),
                self.FILTER_DEFAULTS["sort"],
            ),
        )

        return [
            (key, label, value)
            for key, label, value, default in values
            if value != default
        ]

    def _update_filter_state(self) -> None:
        active_filters = self._get_active_filters()
        active_count = len(active_filters)

        if active_count == 0:
            self.active_filter_badge.configure(
                text="No filters active",
                background=Colors.SURFACE_ALT,
                foreground=Colors.TEXT_MUTED,
            )
            self.reset_filter_button.configure(state="disabled")
            self.active_filter_row.grid_remove()
            self._clear_filter_chips()
            return

        self.active_filter_badge.configure(
            text=(
                "1 active"
                if active_count == 1
                else f"{active_count} active"
            ),
            background=Colors.ACCENT_SOFT,
            foreground=Colors.TEXT,
        )
        self.reset_filter_button.configure(state="normal")
        self._rebuild_filter_chips(active_filters)

        if self._filters_expanded:
            self.active_filter_row.grid(
                row=2,
                column=0,
                sticky="ew",
                pady=(12, 0),
            )

    def _clear_filter_chips(self) -> None:
        for chip in self._chip_widgets:
            chip.destroy()

        self._chip_widgets.clear()

    def _rebuild_filter_chips(self, active_filters) -> None:
        self._clear_filter_chips()

        for index, (key, label, value) in enumerate(active_filters):
            chip = tk.Label(
                self.filter_chip_frame,
                text=f"{label}: {value}  ×",
                background=Colors.ACCENT_SOFT,
                foreground=Colors.TEXT,
                activebackground=Colors.ACCENT_HOVER,
                activeforeground="#FFFFFF",
                font=Fonts.SMALL_BOLD,
                padx=10,
                pady=5,
                cursor="hand2",
                borderwidth=0,
            )
            chip.pack(
                side="left",
                padx=(0 if index == 0 else 6, 0),
            )
            chip.bind(
                "<Button-1>",
                lambda _event, filter_key=key: (
                    self._clear_filter(filter_key)
                ),
            )
            chip.bind(
                "<Enter>",
                lambda _event, widget=chip: widget.configure(
                    background=Colors.ACCENT_HOVER
                ),
            )
            chip.bind(
                "<Leave>",
                lambda _event, widget=chip: widget.configure(
                    background=Colors.ACCENT_SOFT
                ),
            )

            self._chip_widgets.append(chip)

    def _clear_filter(self, key: str) -> None:
        variable_map = {
            "title": self.filter_title_var,
            "platform": self.platform_var,
            "year": self.year_var,
            "genre": self.genre_var,
            "cover": self.cover_var,
            "sort": self.sort_var,
        }

        variable_map[key].set(self.FILTER_DEFAULTS[key])
        self._apply_discovery_filters()

    # ---------------------------------------------------------
    # Results and details
    # ---------------------------------------------------------

    def _display_results(self, games, filtered=False) -> None:
        self.results = games
        self._clear_results_table()
        self.save_button.configure(state="disabled")
        self.page_label.configure(
            text=f"Page {self.current_page}"
        )
        self.result_count_label.configure(
            text=(
                "1 game"
                if len(games) == 1
                else f"{len(games)} games"
            )
        )

        if not games:
            if filtered and self.page_results:
                self.status_label.configure(
                    text=(
                        "No games match the selected filters "
                        f"on page {self.current_page}."
                    )
                )
                self._set_details(
                    "No games match the selected filters.\n\n"
                    "Remove a filter chip or press Reset to show "
                    "more results."
                )
            else:
                self.status_label.configure(
                    text=f"No results on page {self.current_page}."
                )
                self._set_details(
                    "No games were found on this page."
                )

            self._update_pagination_state()
            return

        for index, game in enumerate(games):
            title = game.get("name", "Unknown Title")
            platform = (
                self.discovery_filter_service.get_platform_text(
                    game
                )
            )
            release_date = (
                self.discovery_filter_service
                .get_release_date_text(game)
            )

            self.results_table.insert(
                "",
                tk.END,
                iid=str(index),
                values=(title, platform, release_date),
            )

        if filtered:
            self.status_label.configure(
                text=(
                    f"Showing {len(games)} of "
                    f"{len(self.page_results)} games on "
                    f"page {self.current_page}."
                )
            )
        elif self.current_mode == "search":
            self.status_label.configure(
                text=(
                    f'Searching “{self.current_search_term}” — '
                    f"{len(games)} results on this page."
                )
            )
        else:
            self.status_label.configure(
                text=(
                    f"Browsing games — {len(games)} results "
                    "on this page."
                )
            )

        self._set_details(
            f"Found {len(games)} results on page "
            f"{self.current_page}.\n\n"
            "Select a game to preview its metadata."
        )
        self._update_pagination_state()

    def _clear_results_table(self) -> None:
        for row in self.results_table.get_children():
            self.results_table.delete(row)

    def _on_game_selected(self, _event=None) -> None:
        selected_game = self._get_selected_game()

        if not selected_game:
            self.save_button.configure(state="disabled")
            return

        title = selected_game.get("name", "Unknown Title")
        platform = (
            self.discovery_filter_service.get_platform_text(
                selected_game
            )
        )
        release_date = (
            self.discovery_filter_service.get_release_date_text(
                selected_game
            )
        )
        genres = self.discovery_filter_service.get_genre_text(
            selected_game
        )
        summary = selected_game.get(
            "summary",
            "No summary available.",
        )
        storyline = selected_game.get("storyline", "")

        details = (
            f"{title}\n"
            f"{'─' * min(len(title), 32)}\n\n"
            f"Platform\n{platform}\n\n"
            f"Release date\n{release_date}\n\n"
            f"Genres\n{genres}\n\n"
            f"Summary\n{summary}\n"
        )

        if storyline:
            details += f"\nStoryline\n{storyline}\n"

        self._set_details(details)
        self.save_button.configure(state="normal")

    def _set_details(self, text: str) -> None:
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, text)
        self.details_text.configure(state="disabled")
        self.details_text.yview_moveto(0)

    def _save_selected_game(self) -> None:
        selected_game = self._get_selected_game()

        if not selected_game:
            messagebox.showwarning(
                "No Game Selected",
                "Please select a game first.",
                parent=self,
            )
            return

        try:
            saved_game = self.game_repository.add_game(
                selected_game
            )
            messagebox.showinfo(
                "Saved",
                (
                    f"{saved_game.title} has been saved "
                    "to your library."
                ),
                parent=self,
            )
        except Exception as error:
            messagebox.showerror(
                "Save Error",
                str(error),
                parent=self,
            )

    def _get_selected_game(self):
        selected_item = self.results_table.selection()

        if not selected_item:
            return None

        try:
            selected_index = int(selected_item[0])
        except (TypeError, ValueError):
            return None

        if (
            selected_index < 0
            or selected_index >= len(self.results)
        ):
            return None

        return self.results[selected_index]

    def close(self) -> None:
        self.game_repository.close()
