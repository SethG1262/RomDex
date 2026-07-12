import tkinter as tk
from io import BytesIO
from tkinter import ttk

import requests
from PIL import Image, ImageTk


class GameDetailsPanel(ttk.Frame):
    """Displays cover art and metadata for the selected game."""

    COVER_SIZE = (260, 360)

    def __init__(self, parent):
        super().__init__(parent)

        self.cover_image = None

        ttk.Label(
            self,
            text="Game Info",
            font=("Arial", 12, "bold"),
        ).pack(anchor="w")

        self.cover_frame = tk.Frame(
            self,
            width=self.COVER_SIZE[0],
            height=self.COVER_SIZE[1],
            relief="groove",
            borderwidth=2,
        )
        self.cover_frame.pack(pady=(5, 10))
        self.cover_frame.pack_propagate(False)

        self.cover_label = ttk.Label(
            self.cover_frame,
            text="No cover selected",
            anchor="center",
            justify="center",
        )
        self.cover_label.pack(fill="both", expand=True)

        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True)

        self.details_text = tk.Text(
            text_frame,
            width=45,
            height=12,
            wrap="word",
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.details_text.yview,
        )
        self.details_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.details_text.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

    def show_game(self, game):
        self._show_cover(game.cover_url)
        self._set_details(self._build_details(game))

    def clear(self):
        self.cover_frame.pack_forget()
        self.cover_label.configure(
            image="",
            text="No cover selected",
        )
        self.cover_image = None
        self._set_details("")

    def _show_cover(self, cover_url):
        if not cover_url:
            self.cover_frame.pack_forget()
            self.cover_image = None
            return

        self.cover_frame.pack(pady=(5, 10))

        try:
            response = requests.get(
                self._get_large_cover_url(cover_url),
                timeout=10,
            )
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            image = image.resize(
                self.COVER_SIZE,
                Image.LANCZOS,
            )

            self.cover_image = ImageTk.PhotoImage(image)
            self.cover_label.configure(
                image=self.cover_image,
                text="",
            )
        except Exception as error:
            self.cover_image = None
            self.cover_label.configure(
                image="",
                text=f"Cover failed to load\n{error}",
            )

    def _set_details(self, details):
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details)

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
