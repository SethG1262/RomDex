import tkinter as tk
from tkinter import ttk, messagebox

from services.igdb_service import IGDBService
from services.discovery_filter_service import DiscoveryFilterService
from repositories.game_repository import GameRepository


class DiscoveryFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.igdb_service = IGDBService()
        self.game_repository = GameRepository()
        self.discovery_filter_service = DiscoveryFilterService()

        # Full unfiltered results for the current IGDB page
        self.page_results = []

        # Filtered results currently displayed in the table
        self.results = []

        self.page_size = 50
        self.current_offset = 0
        self.current_page = 1
        self.current_mode = None
        self.current_search_term = ""

        self._create_widgets()

    def _create_widgets(self):
        title_label = ttk.Label(
            self,
            text="Discover Nintendo DS / DSi / 3DS Games",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)

        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill="x")

        self.search_entry = ttk.Entry(search_frame, width=45)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind(
            "<Return>",
            lambda event: self._start_search()
        )

        search_button = ttk.Button(
            search_frame,
            text="Search",
            command=self._start_search
        )
        search_button.pack(side="left", padx=5)

        browse_button = ttk.Button(
            search_frame,
            text="Browse",
            command=self._start_browse
        )
        browse_button.pack(side="left", padx=5)

        # Advanced filters for the current IGDB result page
        filter_frame = ttk.LabelFrame(
            self,
            text="Discovery Filters",
            padding=10
        )
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))

        first_filter_row = ttk.Frame(filter_frame)
        first_filter_row.pack(fill="x", pady=(0, 6))

        ttk.Label(
            first_filter_row,
            text="Filter title:"
        ).pack(side="left")

        self.filter_title_entry = ttk.Entry(
            first_filter_row,
            width=24
        )
        self.filter_title_entry.pack(
            side="left",
            padx=(5, 12)
        )
        self.filter_title_entry.bind(
            "<Return>",
            lambda event: self._apply_discovery_filters()
        )

        ttk.Label(
            first_filter_row,
            text="Platform:"
        ).pack(side="left")

        self.platform_filter = ttk.Combobox(
            first_filter_row,
            state="readonly",
            width=18,
            values=["All Platforms"]
        )
        self.platform_filter.set("All Platforms")
        self.platform_filter.pack(
            side="left",
            padx=(5, 12)
        )

        ttk.Label(
            first_filter_row,
            text="Year:"
        ).pack(side="left")

        self.year_filter = ttk.Combobox(
            first_filter_row,
            state="readonly",
            width=11,
            values=["All Years"]
        )
        self.year_filter.set("All Years")
        self.year_filter.pack(
            side="left",
            padx=(5, 12)
        )

        second_filter_row = ttk.Frame(filter_frame)
        second_filter_row.pack(fill="x")

        ttk.Label(
            second_filter_row,
            text="Genre:"
        ).pack(side="left")

        self.genre_filter = ttk.Combobox(
            second_filter_row,
            state="readonly",
            width=18,
            values=["All Genres"]
        )
        self.genre_filter.set("All Genres")
        self.genre_filter.pack(
            side="left",
            padx=(5, 12)
        )

        ttk.Label(
            second_filter_row,
            text="Cover:"
        ).pack(side="left")

        self.cover_filter = ttk.Combobox(
            second_filter_row,
            state="readonly",
            width=12,
            values=[
                "All Games",
                "Has Cover",
                "No Cover"
            ]
        )
        self.cover_filter.set("All Games")
        self.cover_filter.pack(
            side="left",
            padx=(5, 12)
        )

        ttk.Label(
            second_filter_row,
            text="Sort:"
        ).pack(side="left")

        self.sort_filter = ttk.Combobox(
            second_filter_row,
            state="readonly",
            width=20,
            values=[
                "Title A-Z",
                "Title Z-A",
                "Release Year Newest",
                "Release Year Oldest"
            ]
        )
        self.sort_filter.set("Title A-Z")
        self.sort_filter.pack(
            side="left",
            padx=(5, 12)
        )

        apply_filter_button = ttk.Button(
            second_filter_row,
            text="Apply Filters",
            command=self._apply_discovery_filters
        )
        apply_filter_button.pack(side="left", padx=5)

        reset_filter_button = ttk.Button(
            second_filter_row,
            text="Reset Filters",
            command=self._reset_discovery_filters
        )
        reset_filter_button.pack(side="left", padx=5)

        # Automatically update results when a dropdown changes
        for combobox in (
            self.platform_filter,
            self.year_filter,
            self.genre_filter,
            self.cover_filter,
            self.sort_filter
        ):
            combobox.bind(
                "<<ComboboxSelected>>",
                lambda event: self._apply_discovery_filters()
            )

        page_frame = ttk.Frame(self, padding=(10, 0))
        page_frame.pack(fill="x")

        previous_button = ttk.Button(
            page_frame,
            text="Previous Page",
            command=self._previous_page
        )
        previous_button.pack(side="left", padx=(0, 5))

        next_button = ttk.Button(
            page_frame,
            text="Next Page",
            command=self._next_page
        )
        next_button.pack(side="left", padx=5)

        self.page_label = ttk.Label(
            page_frame,
            text="Page: 1"
        )
        self.page_label.pack(side="left", padx=10)

        self.status_label = ttk.Label(
            page_frame,
            text="Search or browse to load games."
        )
        self.status_label.pack(side="left", padx=10)

        content_frame = ttk.Frame(self, padding=10)
        content_frame.pack(fill="both", expand=True)

        columns = ("title", "platform", "release_date")

        self.results_table = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings"
        )

        self.results_table.heading("title", text="Title")
        self.results_table.heading("platform", text="Platform")
        self.results_table.heading("release_date", text="Release Date")

        self.results_table.column("title", width=360)
        self.results_table.column("platform", width=220)
        self.results_table.column("release_date", width=130)

        self.results_table.pack(side="left", fill="both", expand=True)

        self.results_table.bind("<<TreeviewSelect>>", self._on_game_selected)

        details_frame = ttk.Frame(content_frame, padding=(10, 0))
        details_frame.pack(side="right", fill="both")

        details_label = ttk.Label(details_frame, text="Game Details")
        details_label.pack(anchor="w")

        self.details_text = tk.Text(
            details_frame,
            width=42,
            height=22,
            wrap="word"
        )
        self.details_text.pack(fill="both", expand=True, pady=(5, 10))

        save_button = ttk.Button(
            details_frame,
            text="Save Selected to Library",
            command=self._save_selected_game
        )
        save_button.pack(fill="x")

    def _start_search(self):
        search_term = self.search_entry.get().strip()

        if not search_term:
            messagebox.showwarning("Missing Search", "Please enter a game title.")
            return

        self.current_mode = "search"
        self.current_search_term = search_term
        self.current_offset = 0
        self.current_page = 1

        self._load_current_page()

    def _start_browse(self):
        self.current_mode = "browse"
        self.current_search_term = ""
        self.current_offset = 0
        self.current_page = 1

        self._load_current_page()

    def _next_page(self):
        if not self.current_mode:
            messagebox.showinfo("No Search", "Search or browse first.")
            return

        self.current_offset += self.page_size
        self.current_page += 1

        self._load_current_page()

    def _previous_page(self):
        if not self.current_mode:
            messagebox.showinfo("No Search", "Search or browse first.")
            return

        if self.current_offset == 0:
            return

        self.current_offset -= self.page_size
        self.current_page -= 1

        self._load_current_page()

    def _load_current_page(self):
        try:
            self._set_loading_state()

            if self.current_mode == "search":
                games = self.igdb_service.search_ds_family_games_page(
                    self.current_search_term,
                    limit=self.page_size,
                    offset=self.current_offset
                )

            elif self.current_mode == "browse":
                games = self.igdb_service.get_ds_family_games_page(
                    limit=self.page_size,
                    offset=self.current_offset
                )

            else:
                games = []

            # Preserve the original page before applying local filters
            self.page_results = games

            self._refresh_discovery_filter_options()
            self._reset_discovery_filters()

        except Exception as error:
            messagebox.showerror("IGDB Error", str(error))

    def _set_loading_state(self):
        for row in self.results_table.get_children():
            self.results_table.delete(row)

        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, "Loading games from IGDB...")

        self.status_label.config(text="Loading...")

    def _apply_discovery_filters(self):
        filtered_games = self.discovery_filter_service.filter_games(
            games=self.page_results,
            title=self.filter_title_entry.get(),
            platform=self.platform_filter.get(),
            release_year=self.year_filter.get(),
            genre=self.genre_filter.get(),
            cover_option=self.cover_filter.get(),
            sort_option=self.sort_filter.get()
        )

        self._display_results(filtered_games, filtered=True)

    def _reset_discovery_filters(self):
        self.filter_title_entry.delete(0, tk.END)

        self.platform_filter.set("All Platforms")
        self.year_filter.set("All Years")
        self.genre_filter.set("All Genres")
        self.cover_filter.set("All Games")
        self.sort_filter.set("Title A-Z")

        default_results = self.discovery_filter_service.filter_games(
            games=self.page_results,
            sort_option="Title A-Z"
        )

        self._display_results(default_results, filtered=False)

    def _refresh_discovery_filter_options(self):
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

        self.platform_filter["values"] = platform_options
        self.year_filter["values"] = year_options
        self.genre_filter["values"] = genre_options

    def _display_results(self, games, filtered=False):
        self.results = games

        for row in self.results_table.get_children():
            self.results_table.delete(row)

        self.details_text.delete("1.0", tk.END)

        self.page_label.config(text=f"Page: {self.current_page}")

        if not games:
            if filtered and self.page_results:
                self.status_label.config(
                    text=(
                        f"No games match the selected filters on "
                        f"page {self.current_page}."
                    )
                )
                self.details_text.insert(
                    tk.END,
                    "No games match the selected filters."
                )
            else:
                self.status_label.config(
                    text=f"No results on page {self.current_page}."
                )
                self.details_text.insert(
                    tk.END,
                    "No games found on this page."
                )
            return

        for index, game in enumerate(games):
            title = game.get("name", "Unknown Title")
            platform = self.discovery_filter_service.get_platform_text(game)
            release_date = (
                self.discovery_filter_service.get_release_date_text(game)
            )

            self.results_table.insert(
                "",
                tk.END,
                iid=str(index),
                values=(title, platform, release_date)
            )

        if filtered:
            self.status_label.config(
                text=(
                    f"Showing {len(games)} of {len(self.page_results)} "
                    f"game(s) on page {self.current_page}."
                )
            )
        elif self.current_mode == "search":
            self.status_label.config(
                text=(
                    f'Searching "{self.current_search_term}" — '
                    f'{len(games)} result(s) on this page.'
                )
            )
        else:
            self.status_label.config(
                text=(
                    f"Browsing games — {len(games)} "
                    f"result(s) on this page."
                )
            )

        self.details_text.insert(
            tk.END,
            f"Found {len(games)} result(s) on page {self.current_page}.\n\n"
            "Select a game to view details."
        )

    def _on_game_selected(self, event):
        selected_game = self._get_selected_game()

        if not selected_game:
            return

        title = selected_game.get("name", "Unknown Title")
        platform = self.discovery_filter_service.get_platform_text(selected_game)
        release_date = (
            self.discovery_filter_service.get_release_date_text(selected_game)
        )
        genres = self.discovery_filter_service.get_genre_text(selected_game)
        summary = selected_game.get("summary", "No summary available.")
        storyline = selected_game.get("storyline", "")

        details = f"Title: {title}\n\n"
        details += f"Platform: {platform}\n\n"
        details += f"Release Date: {release_date}\n\n"
        details += f"Genres: {genres}\n\n"
        details += f"Summary:\n{summary}\n\n"

        if storyline:
            details += f"Storyline:\n{storyline}\n\n"

        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details)

    def _save_selected_game(self):
        selected_game = self._get_selected_game()

        if not selected_game:
            messagebox.showwarning("No Game Selected", "Please select a game first.")
            return

        try:
            saved_game = self.game_repository.add_game(selected_game)

            messagebox.showinfo(
                "Saved",
                f"{saved_game.title} has been saved to your library."
            )

        except Exception as error:
            messagebox.showerror("Save Error", str(error))

    def _get_selected_game(self):
        selected_item = self.results_table.selection()

        if not selected_item:
            return None

        selected_index = int(selected_item[0])

        if selected_index < 0 or selected_index >= len(self.results):
            return None

        return self.results[selected_index]

    def close(self):
        self.game_repository.close()
