import tkinter as tk
from io import BytesIO
from tkinter import ttk

import requests
from PIL import Image, ImageTk


class GameDetailsPanel(ttk.Frame):
    """
    Responsive cover art and metadata panel.

    The cover becomes smaller when vertical space is limited so the
    Library action bar does not get pushed out of the window.
    """

    LARGE_COVER_SIZE = (210, 294)
    COMPACT_COVER_SIZE = (135, 189)
    COMPACT_HEIGHT_THRESHOLD = 440

    def __init__(self, parent):
        super().__init__(parent, style="Surface.TFrame")

        self.cover_image = None
        self._source_cover_image = None
        self._current_cover_size = None
        self._has_cover = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(
            self,
            text="Game Details",
            style="SectionTitle.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 8),
        )

        self.cover_frame = tk.Frame(
            self,
            width=self.LARGE_COVER_SIZE[0],
            height=self.LARGE_COVER_SIZE[1],
            relief="flat",
            borderwidth=0,
        )
        self.cover_frame.grid(
            row=1,
            column=0,
            pady=(0, 10),
        )
        self.cover_frame.grid_propagate(False)

        self.cover_label = ttk.Label(
            self.cover_frame,
            text="No cover selected",
            anchor="center",
            justify="center",
            style="Surface.TLabel",
        )
        self.cover_label.pack(fill="both", expand=True)

        text_frame = ttk.Frame(
            self,
            style="Surface.TFrame",
        )
        text_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.details_text = tk.Text(
            text_frame,
            width=34,
            height=5,
            wrap="word",
            state="disabled",
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.details_text.yview,
        )
        self.details_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.details_text.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.bind("<Configure>", self._on_resize)
        self.clear()

    def show_game(self, game):
        self._show_cover(game.cover_url)
        self._set_details(self._build_details(game))

    def clear(self):
        self._has_cover = False
        self._source_cover_image = None
        self.cover_frame.grid_remove()
        self.cover_label.configure(
            image="",
            text="No cover selected",
        )
        self.cover_image = None
        self._set_details(
            "Select a game from the library to view its details."
        )

    def _show_cover(self, cover_url):
        if not cover_url:
            self._has_cover = False
            self._source_cover_image = None
            self.cover_frame.grid_remove()
            self.cover_image = None
            return

        self._has_cover = True
        self.cover_frame.grid()

        try:
            response = requests.get(
                self._get_large_cover_url(cover_url),
                timeout=10,
            )
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            self._source_cover_image = image.convert("RGB")
            self._render_cover(self._get_target_cover_size())
        except Exception as error:
            self._source_cover_image = None
            self.cover_image = None
            self.cover_label.configure(
                image="",
                text=f"Cover failed to load\n{error}",
            )

    def _on_resize(self, event):
        if not self._has_cover or self._source_cover_image is None:
            return

        target_size = self._get_target_cover_size(event.height)

        if target_size != self._current_cover_size:
            self._render_cover(target_size)

    def _get_target_cover_size(self, panel_height=None):
        if panel_height is None:
            panel_height = self.winfo_height()

        if panel_height < self.COMPACT_HEIGHT_THRESHOLD:
            return self.COMPACT_COVER_SIZE

        return self.LARGE_COVER_SIZE

    def _render_cover(self, target_size):
        if self._source_cover_image is None:
            return

        resized_image = self._source_cover_image.resize(
            target_size,
            Image.LANCZOS,
        )

        self.cover_image = ImageTk.PhotoImage(resized_image)
        self._current_cover_size = target_size

        self.cover_frame.configure(
            width=target_size[0],
            height=target_size[1],
        )
        self.cover_label.configure(
            image=self.cover_image,
            text="",
        )

    def _set_details(self, details):
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details)
        self.details_text.configure(state="disabled")
        self.details_text.yview_moveto(0)

    @staticmethod
    def _build_details(game):
        has_local_rom = bool(game.rom_path)
        has_igdb_metadata = bool(game.igdb_id)

        if has_local_rom and has_igdb_metadata:
            game_type = "Local ROM + IGDB Metadata"
        elif has_local_rom:
            game_type = "Local ROM Only"
        elif has_igdb_metadata:
            game_type = "IGDB Metadata Only"
        else:
            game_type = "Manual Entry"

        details = (
            f"Title: {game.title}\n\n"
            f"Platform: {game.platform or 'Unknown'}\n\n"
            f"Status: {game.status or 'Unknown'}\n\n"
            f"Type: {game_type}\n\n"
            "Local File Info:\n"
        )

        if has_local_rom:
            details += (
                f"File Name: {game.file_name or 'Unknown'}\n"
                f"ROM Path:\n{game.rom_path}\n\n"
            )
        else:
            details += "No local ROM file attached.\n\n"

        details += "IGDB Metadata:\n"

        if has_igdb_metadata:
            details += (
                f"IGDB ID: {game.igdb_id}\n"
                f"Release Date: "
                f"{game.release_year or 'Unknown'}\n\n"
                f"Summary:\n"
                f"{game.summary or 'No summary available.'}\n\n"
            )

            if game.storyline:
                details += f"Storyline:\n{game.storyline}\n\n"

            if game.cover_url:
                details += f"Cover URL:\n{game.cover_url}\n"
        else:
            details += "Not matched with IGDB yet.\n"

        return details

    @staticmethod
    def _get_large_cover_url(cover_url):
        if "t_cover_big_2x" in cover_url:
            return cover_url

        for size in (
            "t_thumb",
            "t_cover_small",
            "t_cover_big",
        ):
            if size in cover_url:
                return cover_url.replace(
                    size,
                    "t_cover_big_2x",
                )

        return cover_url
