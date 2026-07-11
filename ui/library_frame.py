import tkinter as tk
from io import BytesIO
from tkinter import filedialog, messagebox, ttk

import requests
from PIL import Image, ImageTk

from repositories.game_repository import GameRepository
from services.library_filter_service import LibraryFilterService


class LibraryFrame(ttk.Frame):
    """
    Library tab for RomDex.

    This frame owns the local library UI, filtering, cover display,
    ROM importing, deletion, and local GameRepository connection.
    """

    SEARCH_PLACEHOLDER = "Search games..."

    def __init__(
        self,
        parent,
        on_discover_requested=None,
        on_quit_requested=None
    ):
        super().__init__(parent)

        self.on_discover_requested = (
            on_discover_requested
        )
        self.on_quit_requested = (
            on_quit_requested
        )

        self.game_repository = GameRepository()
        self.library_filter_service = (
            LibraryFilterService()
        )
        self.cover_image = None

        self._create_widgets()
        self.refresh_library()

    def _create_widgets(self):
        title_label = tk.Label(
            self,
            text="DS ROM Library",
            font=("Arial", 22, "bold")
        )
        title_label.pack(pady=15)

        self._create_action_bar()
        self._create_filter_bar()
        self._create_content_area()
        self._create_bottom_bar()

    def _create_action_bar(self):
        top_frame = tk.Frame(self)
        top_frame.pack(
            fill="x",
            padx=20
        )

        self.search_entry = tk.Entry(
            top_frame,
            width=40
        )
        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True
        )
        self.search_entry.insert(
            0,
            self.SEARCH_PLACEHOLDER
        )
        self.search_entry.bind(
            "<Return>",
            lambda event: self.apply_filters()
        )
        self.search_entry.bind(
            "<FocusIn>",
            self._clear_search_placeholder
        )

        tk.Button(
            top_frame,
            text="Apply Filters",
            command=self.apply_filters
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            top_frame,
            text="Reset Filters",
            command=self.reset_filters
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            top_frame,
            text="Add Game",
            command=self.add_game
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            top_frame,
            text="Discover IGDB",
            command=self._open_discovery
        ).pack(
            side="left",
            padx=5
        )

    def _create_filter_bar(self):
        filter_frame = ttk.LabelFrame(
            self,
            text="Advanced Filters",
            padding=10
        )
        filter_frame.pack(
            fill="x",
            padx=20,
            pady=(10, 0)
        )

        ttk.Label(
            filter_frame,
            text="Platform:"
        ).pack(side="left")

        self.platform_filter = ttk.Combobox(
            filter_frame,
            state="readonly",
            width=18,
            values=["All Platforms"]
        )
        self.platform_filter.set(
            "All Platforms"
        )
        self.platform_filter.pack(
            side="left",
            padx=(5, 15)
        )

        ttk.Label(
            filter_frame,
            text="Type:"
        ).pack(side="left")

        self.type_filter = ttk.Combobox(
            filter_frame,
            state="readonly",
            width=15,
            values=[
                "All Types",
                "Local ROM",
                "IGDB",
                "Local + IGDB",
                "Manual"
            ]
        )
        self.type_filter.set("All Types")
        self.type_filter.pack(
            side="left",
            padx=(5, 15)
        )

        ttk.Label(
            filter_frame,
            text="Status:"
        ).pack(side="left")

        self.status_filter = ttk.Combobox(
            filter_frame,
            state="readonly",
            width=15,
            values=["All Statuses"]
        )
        self.status_filter.set(
            "All Statuses"
        )
        self.status_filter.pack(
            side="left",
            padx=(5, 15)
        )

        ttk.Label(
            filter_frame,
            text="Sort:"
        ).pack(side="left")

        self.sort_filter = ttk.Combobox(
            filter_frame,
            state="readonly",
            width=15,
            values=[
                "Title A-Z",
                "Title Z-A",
                "Newest Added",
                "Oldest Added"
            ]
        )
        self.sort_filter.set("Title A-Z")
        self.sort_filter.pack(
            side="left",
            padx=5
        )

        for combobox in (
            self.platform_filter,
            self.type_filter,
            self.status_filter,
            self.sort_filter
        ):
            combobox.bind(
                "<<ComboboxSelected>>",
                lambda event: self.apply_filters()
            )

    def _create_content_area(self):
        content_frame = tk.Frame(self)
        content_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        columns = (
            "title",
            "platform",
            "type",
            "status"
        )

        self.game_table = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings"
        )

        self.game_table.heading(
            "title",
            text="Title"
        )
        self.game_table.heading(
            "platform",
            text="Platform"
        )
        self.game_table.heading(
            "type",
            text="Type"
        )
        self.game_table.heading(
            "status",
            text="Status"
        )

        self.game_table.column(
            "title",
            width=300
        )
        self.game_table.column(
            "platform",
            width=150
        )
        self.game_table.column(
            "type",
            width=140
        )
        self.game_table.column(
            "status",
            width=100
        )

        self.game_table.pack(
            side="left",
            fill="both",
            expand=True
        )
        self.game_table.bind(
            "<<TreeviewSelect>>",
            self._on_game_selected
        )

        details_frame = tk.Frame(
            content_frame
        )
        details_frame.pack(
            side="right",
            fill="both",
            padx=(15, 0)
        )

        tk.Label(
            details_frame,
            text="Game Info",
            font=("Arial", 12, "bold")
        ).pack(anchor="w")

        self.cover_frame = tk.Frame(
            details_frame,
            width=260,
            height=360,
            relief="groove",
            borderwidth=2
        )
        self.cover_frame.pack(
            pady=(5, 10)
        )
        self.cover_frame.pack_propagate(
            False
        )

        self.cover_label = tk.Label(
            self.cover_frame,
            text="No cover selected"
        )
        self.cover_label.pack(
            fill="both",
            expand=True
        )

        self.details_text = tk.Text(
            details_frame,
            width=45,
            height=12,
            wrap="word"
        )
        self.details_text.pack(
            fill="both",
            expand=True
        )

    def _create_bottom_bar(self):
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        tk.Button(
            bottom_frame,
            text="Delete Selected",
            command=self.delete_selected
        ).pack(side="left")

        tk.Button(
            bottom_frame,
            text="Refresh Library",
            command=self.refresh_library
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            bottom_frame,
            text="Quit",
            command=self._quit
        ).pack(side="right")

    def _clear_search_placeholder(
        self,
        event
    ):
        if (
            self.search_entry.get()
            == self.SEARCH_PLACEHOLDER
        ):
            self.search_entry.delete(
                0,
                tk.END
            )

    def apply_filters(self):
        search_text = (
            self.search_entry.get().strip()
        )

        if (
            search_text
            == self.SEARCH_PLACEHOLDER
        ):
            search_text = ""

        games = (
            self.game_repository
            .get_all_games()
        )

        filtered_games = (
            self.library_filter_service
            .filter_games(
                games=games,
                search_text=search_text,
                platform=(
                    self.platform_filter.get()
                ),
                game_type=(
                    self.type_filter.get()
                ),
                status=(
                    self.status_filter.get()
                ),
                sort_option=(
                    self.sort_filter.get()
                )
            )
        )

        self._display_games(
            filtered_games
        )

    def reset_filters(self):
        self.search_entry.delete(
            0,
            tk.END
        )
        self.search_entry.insert(
            0,
            self.SEARCH_PLACEHOLDER
        )

        self.platform_filter.set(
            "All Platforms"
        )
        self.type_filter.set(
            "All Types"
        )
        self.status_filter.set(
            "All Statuses"
        )
        self.sort_filter.set(
            "Title A-Z"
        )

        self.refresh_library()

    def _refresh_filter_options(
        self,
        games
    ):
        platform_options = (
            self.library_filter_service
            .get_platform_options(games)
        )
        status_options = (
            self.library_filter_service
            .get_status_options(games)
        )

        current_platform = (
            self.platform_filter.get()
        )
        current_status = (
            self.status_filter.get()
        )

        self.platform_filter[
            "values"
        ] = platform_options
        self.status_filter[
            "values"
        ] = status_options

        if (
            current_platform
            not in platform_options
        ):
            self.platform_filter.set(
                "All Platforms"
            )

        if (
            current_status
            not in status_options
        ):
            self.status_filter.set(
                "All Statuses"
            )

    def add_game(self):
        rom_paths = (
            filedialog.askopenfilenames(
                title=(
                    "Select Nintendo DS "
                    "ROM files"
                ),
                filetypes=[
                    (
                        "Nintendo DS ROMs",
                        "*.nds"
                    ),
                    (
                        "All Files",
                        "*.*"
                    )
                ]
            )
        )

        if not rom_paths:
            return

        added_count = 0
        skipped_count = 0

        try:
            for rom_path in rom_paths:
                if not rom_path.lower().endswith(
                    ".nds"
                ):
                    skipped_count += 1
                    continue

                existing_game = (
                    self.game_repository
                    .get_game_by_rom_path(
                        rom_path
                    )
                )

                if existing_game:
                    skipped_count += 1
                    continue

                self.game_repository.add_local_rom(
                    rom_path
                )
                added_count += 1

            self.refresh_library()

            messagebox.showinfo(
                "Add Game Complete",
                f"Added {added_count} "
                f"game file(s).\n"
                f"Skipped {skipped_count} "
                f"file(s)."
            )

        except Exception as error:
            messagebox.showerror(
                "Add Game Error",
                str(error)
            )

    def delete_selected(self):
        selected_item = (
            self.game_table.selection()
        )

        if not selected_item:
            messagebox.showwarning(
                "No Selection",
                "Please select a game first."
            )
            return

        confirmed = messagebox.askyesno(
            "Delete Game",
            "Are you sure you want to "
            "delete the selected game?"
        )

        if not confirmed:
            return

        game_id = int(
            selected_item[0]
        )

        try:
            self.game_repository.delete_game(
                game_id
            )
            self.refresh_library()

        except Exception as error:
            messagebox.showerror(
                "Delete Error",
                str(error)
            )

    def _on_game_selected(self, event):
        selected_item = (
            self.game_table.selection()
        )

        if not selected_item:
            return

        game_id = int(
            selected_item[0]
        )
        game = (
            self.game_repository
            .get_game_by_id(game_id)
        )

        if not game:
            return

        if game.cover_url:
            self.cover_frame.pack(
                pady=(5, 10)
            )
            self._load_cover_art(
                game.cover_url
            )
        else:
            self.cover_frame.pack_forget()
            self.cover_image = None

        details = self._build_game_details(
            game
        )

        self.details_text.delete(
            "1.0",
            tk.END
        )
        self.details_text.insert(
            tk.END,
            details
        )

    def _build_game_details(self, game):
        has_local_rom = bool(
            game.rom_path
        )
        has_igdb_metadata = bool(
            game.igdb_id
        )

        if (
            has_local_rom
            and has_igdb_metadata
        ):
            game_type = (
                "Local ROM + IGDB Metadata"
            )
        elif has_local_rom:
            game_type = "Local ROM Only"
        elif has_igdb_metadata:
            game_type = (
                "IGDB Metadata Only"
            )
        else:
            game_type = "Manual Entry"

        details = (
            f"Title: {game.title}\n\n"
            f"Platform: "
            f"{game.platform or 'Unknown'}\n\n"
            f"Status: "
            f"{game.status or 'Unknown'}\n\n"
            f"Type: {game_type}\n\n"
            "Local File Info:\n"
        )

        if has_local_rom:
            details += (
                f"File Name: "
                f"{game.file_name or 'Unknown'}\n"
                f"ROM Path:\n"
                f"{game.rom_path}\n\n"
            )
        else:
            details += (
                "No local ROM file attached.\n\n"
            )

        details += "IGDB Metadata:\n"

        if has_igdb_metadata:
            details += (
                f"IGDB ID: {game.igdb_id}\n"
                f"Release Date: "
                f"{game.release_year or 'Unknown'}"
                "\n\n"
                f"Summary:\n"
                f"{game.summary or 'No summary available.'}"
                "\n\n"
            )

            if game.storyline:
                details += (
                    f"Storyline:\n"
                    f"{game.storyline}\n\n"
                )

            if game.cover_url:
                details += (
                    f"Cover URL:\n"
                    f"{game.cover_url}\n"
                )
        else:
            details += (
                "Not matched with IGDB yet.\n"
            )

        return details

    def _load_cover_art(
        self,
        cover_url
    ):
        if not cover_url:
            self.cover_frame.pack_forget()
            self.cover_image = None
            return

        try:
            response = requests.get(
                self._get_large_cover_url(
                    cover_url
                ),
                timeout=10
            )
            response.raise_for_status()

            image = Image.open(
                BytesIO(response.content)
            )
            image = image.resize(
                (260, 360),
                Image.LANCZOS
            )

            self.cover_image = (
                ImageTk.PhotoImage(image)
            )
            self.cover_label.config(
                image=self.cover_image,
                text=""
            )

        except Exception as error:
            self.cover_label.config(
                image="",
                text=(
                    "Cover failed to load\n"
                    f"{error}"
                )
            )
            self.cover_image = None

    @staticmethod
    def _get_large_cover_url(
        cover_url
    ):
        if not cover_url:
            return None

        if "t_cover_big_2x" in cover_url:
            return cover_url

        for size in (
            "t_thumb",
            "t_cover_small",
            "t_cover_big"
        ):
            if size in cover_url:
                return cover_url.replace(
                    size,
                    "t_cover_big_2x"
                )

        return cover_url

    def _display_games(self, games):
        for row in (
            self.game_table.get_children()
        ):
            self.game_table.delete(row)

        self.details_text.delete(
            "1.0",
            tk.END
        )
        self.cover_frame.pack_forget()
        self.cover_image = None

        for game in games:
            game_type = (
                self.library_filter_service
                .get_game_type(game)
            )

            self.game_table.insert(
                "",
                "end",
                iid=str(game.id),
                values=(
                    game.title,
                    game.platform
                    or "Unknown",
                    game_type,
                    game.status
                    or "Saved"
                )
            )

    def refresh_library(self):
        games = (
            self.game_repository
            .get_all_games()
        )

        self._refresh_filter_options(
            games
        )

        filtered_games = (
            self.library_filter_service
            .filter_games(
                games=games,
                sort_option="Title A-Z"
            )
        )

        self._display_games(
            filtered_games
        )

    def _open_discovery(self):
        if self.on_discover_requested:
            self.on_discover_requested()

    def _quit(self):
        if self.on_quit_requested:
            self.on_quit_requested()

    def close(self):
        self.game_repository.close()
