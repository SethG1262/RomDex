import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
from io import BytesIO
from PIL import Image, ImageTk

from services.db import init_db
import models.game

from repositories.game_repository import GameRepository
from ui.discovery_frame import DiscoveryFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RomDex")
        self.geometry("1100x700")
        self.minsize(950, 600)

        self.game_repository = GameRepository()
        self.cover_image = None

        self._create_tabs()
        self._create_library_widgets()
        self._create_menu()
        self._load_library_games()

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.library_tab = ttk.Frame(self.notebook)
        self.discovery_tab = DiscoveryFrame(self.notebook)

        self.notebook.add(self.library_tab, text="Library")
        self.notebook.add(self.discovery_tab, text="Discover IGDB")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _create_library_widgets(self):
        title_label = tk.Label(
            self.library_tab,
            text="DS ROM Library",
            font=("Arial", 22, "bold")
        )
        title_label.pack(pady=15)

        top_frame = tk.Frame(self.library_tab)
        top_frame.pack(fill="x", padx=20)

        self.search_entry = tk.Entry(top_frame, width=40)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "Search games...")

        search_button = tk.Button(
            top_frame,
            text="Search",
            command=self._search_games
        )
        search_button.pack(side="left", padx=5)

        add_button = tk.Button(
            top_frame,
            text="Add Game",
            command=self._add_game
        )
        add_button.pack(side="left", padx=5)

        discover_button = tk.Button(
            top_frame,
            text="Discover IGDB",
            command=self._discover_games
        )
        discover_button.pack(side="left", padx=5)

        content_frame = tk.Frame(self.library_tab)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        columns = ("title", "platform", "type", "status")

        self.game_table = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings"
        )

        self.game_table.heading("title", text="Title")
        self.game_table.heading("platform", text="Platform")
        self.game_table.heading("type", text="Type")
        self.game_table.heading("status", text="Status")

        self.game_table.column("title", width=300)
        self.game_table.column("platform", width=150)
        self.game_table.column("type", width=140)
        self.game_table.column("status", width=100)

        self.game_table.pack(side="left", fill="both", expand=True)

        self.game_table.bind("<<TreeviewSelect>>", self._on_library_game_selected)

        details_frame = tk.Frame(content_frame)
        details_frame.pack(side="right", fill="both", padx=(15, 0))

        details_label = tk.Label(
            details_frame,
            text="Game Info",
            font=("Arial", 12, "bold")
        )
        details_label.pack(anchor="w")

        self.cover_frame = tk.Frame(
            details_frame,
            width=260,
            height=360,
            relief="groove",
            borderwidth=2
        )
        self.cover_frame.pack(pady=(5, 10))
        self.cover_frame.pack_propagate(False)

        self.cover_label = tk.Label(
            self.cover_frame,
            text="No cover selected"
        )
        self.cover_label.pack(fill="both", expand=True)

        self.library_details_text = tk.Text(
            details_frame,
            width=45,
            height=12,
            wrap="word"
        )
        self.library_details_text.pack(fill="both", expand=True)

        bottom_frame = tk.Frame(self.library_tab)
        bottom_frame.pack(fill="x", padx=20, pady=10)

        delete_button = tk.Button(
            bottom_frame,
            text="Delete Selected",
            command=self._delete_selected
        )
        delete_button.pack(side="left")

        refresh_button = tk.Button(
            bottom_frame,
            text="Refresh Library",
            command=self._load_library_games
        )
        refresh_button.pack(side="left", padx=5)

        quit_button = tk.Button(
            bottom_frame,
            text="Quit",
            command=self._on_close
        )
        quit_button.pack(side="right")

    def _create_menu(self):
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add Game", command=self._add_game)
        file_menu.add_command(label="Discover IGDB", command=self._discover_games)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Help", command=self._show_help)

        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menu_bar)

    def _search_games(self):
        search_text = self.search_entry.get().strip()

        if not search_text or search_text == "Search games...":
            messagebox.showinfo("Search", "Enter a game title to search.")
            return

        messagebox.showinfo("Search", f"Searching for: {search_text}")

    def _add_game(self):
        rom_paths = filedialog.askopenfilenames(
            title="Select Nintendo DS ROM files",
            filetypes=[
                ("Nintendo DS ROMs", "*.nds"),
                ("All Files", "*.*")
            ]
        )

        if not rom_paths:
            return

        added_count = 0
        skipped_count = 0

        try:
            for rom_path in rom_paths:
                if not rom_path.lower().endswith(".nds"):
                    skipped_count += 1
                    continue

                existing_game = self.game_repository.get_game_by_rom_path(rom_path)

                if existing_game:
                    skipped_count += 1
                    continue

                self.game_repository.add_local_rom(rom_path)
                added_count += 1

            self._load_library_games()

            messagebox.showinfo(
                "Add Game Complete",
                f"Added {added_count} game file(s).\n"
                f"Skipped {skipped_count} file(s)."
            )

        except Exception as error:
            messagebox.showerror("Add Game Error", str(error))

    def _discover_games(self):
        self.notebook.select(self.discovery_tab)

    def _on_tab_changed(self, event):
        selected_tab = self.notebook.select()

        if selected_tab == str(self.library_tab):
            self._load_library_games()

    def _on_library_game_selected(self, event):
        selected_item = self.game_table.selection()

        if not selected_item:
            return

        game_id = int(selected_item[0])
        game = self.game_repository.get_game_by_id(game_id)

        if not game:
            return

        has_local_rom = bool(game.rom_path)
        has_igdb_metadata = bool(game.igdb_id)

        if game.cover_url:
            self.cover_frame.pack(pady=(5, 10))
            self._load_cover_art(game.cover_url)
        else:
            self.cover_frame.pack_forget()
            self.cover_image = None

        if has_local_rom and has_igdb_metadata:
            game_type = "Local ROM + IGDB Metadata"
        elif has_local_rom:
            game_type = "Local ROM Only"
        elif has_igdb_metadata:
            game_type = "IGDB Metadata Only"
        else:
            game_type = "Manual Entry"

        details = f"Title: {game.title}\n\n"
        details += f"Platform: {game.platform or 'Unknown'}\n\n"
        details += f"Status: {game.status or 'Unknown'}\n\n"
        details += f"Type: {game_type}\n\n"

        details += "Local File Info:\n"

        if has_local_rom:
            details += f"File Name: {game.file_name or 'Unknown'}\n"
            details += f"ROM Path:\n{game.rom_path}\n\n"
        else:
            details += "No local ROM file attached.\n\n"

        details += "IGDB Metadata:\n"

        if has_igdb_metadata:
            details += f"IGDB ID: {game.igdb_id}\n"
            details += f"Release Date: {game.release_year or 'Unknown'}\n\n"
            details += f"Summary:\n{game.summary or 'No summary available.'}\n\n"

            if game.storyline:
                details += f"Storyline:\n{game.storyline}\n\n"

            if game.cover_url:
                details += f"Cover URL:\n{game.cover_url}\n"
        else:
            details += "Not matched with IGDB yet.\n"

        self.library_details_text.delete("1.0", tk.END)
        self.library_details_text.insert(tk.END, details)

    def _get_large_cover_url(self, cover_url):
        if not cover_url:
            return None

        if "t_cover_big_2x" in cover_url:
            return cover_url

        if "t_thumb" in cover_url:
            return cover_url.replace("t_thumb", "t_cover_big_2x")

        if "t_cover_small" in cover_url:
            return cover_url.replace("t_cover_small", "t_cover_big_2x")

        if "t_cover_big" in cover_url:
            return cover_url.replace("t_cover_big", "t_cover_big_2x")

        return cover_url

    def _load_cover_art(self, cover_url):
        if not cover_url:
            self.cover_frame.pack_forget()
            self.cover_image = None
            return

        try:
            large_cover_url = self._get_large_cover_url(cover_url)

            response = requests.get(large_cover_url, timeout=10)
            response.raise_for_status()

            image_data = BytesIO(response.content)
            image = Image.open(image_data)

            image = image.resize((260, 360), Image.LANCZOS)

            self.cover_image = ImageTk.PhotoImage(image)

            self.cover_label.config(
                image=self.cover_image,
                text=""
            )

        except Exception as error:
            self.cover_label.config(
                image="",
                text=f"Cover failed to load\n{error}"
            )
            self.cover_image = None

    def _delete_selected(self):
        selected_item = self.game_table.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a game first.")
            return

        confirm = messagebox.askyesno(
            "Delete Game",
            "Are you sure you want to delete the selected game?"
        )

        if not confirm:
            return

        game_id = int(selected_item[0])

        try:
            self.game_repository.delete_game(game_id)
            self._load_library_games()

        except Exception as error:
            messagebox.showerror("Delete Error", str(error))

    def _load_library_games(self):
        for row in self.game_table.get_children():
            self.game_table.delete(row)

        if hasattr(self, "library_details_text"):
            self.library_details_text.delete("1.0", tk.END)

        if hasattr(self, "cover_frame"):
            self.cover_frame.pack_forget()
            self.cover_image = None

        games = self.game_repository.get_all_games()

        for game in games:
            has_local_rom = bool(game.rom_path)
            has_igdb_metadata = bool(game.igdb_id)

            if has_local_rom and has_igdb_metadata:
                game_type = "Local + IGDB"
            elif has_local_rom:
                game_type = "Local ROM"
            elif has_igdb_metadata:
                game_type = "IGDB"
            else:
                game_type = "Manual"

            self.game_table.insert(
                "",
                "end",
                iid=str(game.id),
                values=(
                    game.title,
                    game.platform or "Unknown",
                    game_type,
                    game.status or "Saved"
                )
            )

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "RomDex\nA prototype for organizing Nintendo DS, DSi, and 3DS games."
        )

    def _show_help(self):
        messagebox.showinfo(
            "Help",
            "Use the Library tab to view saved games.\n"
            "Use Add Game to add local .nds files.\n"
            "Use the Discover IGDB tab to search game metadata."
        )

    def _on_close(self):
        try:
            self.discovery_tab.close()
        except Exception:
            pass

        try:
            self.game_repository.close()
        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":
    init_db()

    app = App()
    app.mainloop()