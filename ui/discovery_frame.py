import tkinter as tk
from tkinter import ttk, messagebox

from services.igdb_service import IGDBService
from repositories.game_repository import GameRepository


class DiscoveryFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.igdb_service = IGDBService()
        self.game_repository = GameRepository()

        self.results = []

        self._create_widgets()

    def _create_widgets(self):
        title_label = ttk.Label(
            self,
            text="Discover Nintendo 3DS / DSi Games",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)

        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill="x")

        self.search_entry = ttk.Entry(search_frame, width=45)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        search_button = ttk.Button(
            search_frame,
            text="Search 3DS + DSi",
            command=self._search_games
        )
        search_button.pack(side="left", padx=5)

        browse_button = ttk.Button(
            search_frame,
            text="Browse All",
            command=self._browse_all_games
        )
        browse_button.pack(side="left", padx=5)

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

        self.results_table.column("title", width=330)
        self.results_table.column("platform", width=180)
        self.results_table.column("release_date", width=120)

        self.results_table.pack(side="left", fill="both", expand=True)

        self.results_table.bind("<<TreeviewSelect>>", self._on_game_selected)

        details_frame = ttk.Frame(content_frame, padding=(10, 0))
        details_frame.pack(side="right", fill="both")

        details_label = ttk.Label(details_frame, text="Game Details")
        details_label.pack(anchor="w")

        self.details_text = tk.Text(
            details_frame,
            width=38,
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

    def _search_games(self):
        search_term = self.search_entry.get().strip()

        if not search_term:
            messagebox.showwarning("Missing Search", "Please enter a game title.")
            return

        try:
            games = self.igdb_service.search_3ds_and_dsi_games(search_term)
            self._display_results(games)

        except Exception as error:
            messagebox.showerror("Search Error", str(error))

    def _browse_all_games(self):
        try:
            games = self.igdb_service.get_3ds_and_dsi_games(limit=50)
            self._display_results(games)

        except Exception as error:
            messagebox.showerror("Browse Error", str(error))

    def _display_results(self, games):
        self.results = games

        for row in self.results_table.get_children():
            self.results_table.delete(row)

        self.details_text.delete("1.0", tk.END)

        if not games:
            messagebox.showinfo("No Results", "No games were found.")
            return

        for index, game in enumerate(games):
            title = game.get("name", "Unknown Title")
            platform = self._get_platform_text(game)
            release_date = self._get_release_date_text(game)

            self.results_table.insert(
                "",
                tk.END,
                iid=str(index),
                values=(title, platform, release_date)
            )

    def _on_game_selected(self, event):
        selected_game = self._get_selected_game()

        if not selected_game:
            return

        title = selected_game.get("name", "Unknown Title")
        platform = self._get_platform_text(selected_game)
        release_date = self._get_release_date_text(selected_game)
        summary = selected_game.get("summary", "No summary available.")
        storyline = selected_game.get("storyline", "")

        details = f"Title: {title}\n\n"
        details += f"Platform: {platform}\n\n"
        details += f"Release Date: {release_date}\n\n"
        details += f"Summary:\n{summary}\n\n"

        if storyline:
            details += f"Storyline:\n{storyline}"

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

    def _get_platform_text(self, game):
        platforms = game.get("platforms")

        if not platforms:
            return "Unknown"

        platform_names = []

        for platform in platforms:
            name = platform.get("name")

            if name:
                platform_names.append(name)

        return ", ".join(platform_names)

    def _get_release_date_text(self, game):
        release_dates = game.get("release_dates")

        if not release_dates:
            return "Unknown"

        first_release = release_dates[0]

        return first_release.get("human", "Unknown")

    def close(self):
        self.game_repository.close()