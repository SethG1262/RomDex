import tkinter as tk
from tkinter import messagebox, ttk

from services.db import init_db
import models.game

from repositories.game_repository import GameRepository
from ui.discovery_frame import DiscoveryFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RomDex")
        self.geometry("1000x650")
        self.minsize(850, 500)

        self.game_repository = GameRepository()

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

        columns = ("title", "platform", "genre", "status")

        self.game_table = ttk.Treeview(
            self.library_tab,
            columns=columns,
            show="headings"
        )

        self.game_table.heading("title", text="Title")
        self.game_table.heading("platform", text="Platform")
        self.game_table.heading("genre", text="Genre")
        self.game_table.heading("status", text="Status")

        self.game_table.column("title", width=250)
        self.game_table.column("platform", width=150)
        self.game_table.column("genre", width=150)
        self.game_table.column("status", width=100)

        self.game_table.pack(fill="both", expand=True, padx=20, pady=20)

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
        messagebox.showinfo("Add Game", "This will open the Add Game window later.")

    def _discover_games(self):
        self.notebook.select(self.discovery_tab)

    def _on_tab_changed(self, event):
        selected_tab = self.notebook.select()

        if selected_tab == str(self.library_tab):
            self._load_library_games()

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

        games = self.game_repository.get_all_games()

        for game in games:
            self.game_table.insert(
                "",
                "end",
                iid=str(game.id),
                values=(
                    game.title,
                    game.platform or "Unknown",
                    "Unknown",
                    "Saved"
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
            "Use the Discover IGDB tab to search game metadata.\n"
            "Use Add Game to manually save a ROM entry later."
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