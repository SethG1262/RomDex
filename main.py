import tkinter as tk
from tkinter import messagebox, ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DS ROM Library")
        self.geometry("800x500")
        self.minsize(700, 400)

        self._create_widgets()
        self._create_menu()

    def _create_widgets(self):
        # Title
        title_label = tk.Label(
            self,
            text="DS ROM Library",
            font=("Arial", 22, "bold")
        )
        title_label.pack(pady=15)

        # Top frame for search and buttons
        top_frame = tk.Frame(self)
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

        # Game list table
        columns = ("title", "platform", "genre", "status")

        self.game_table = ttk.Treeview(
            self,
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

        # Temporary sample data
        self.game_table.insert(
            "",
            "end",
            values=("Pokemon Black", "Nintendo DS", "RPG", "Backlog")
        )

        self.game_table.insert(
            "",
            "end",
            values=("Mario Kart DS", "Nintendo DS", "Racing", "Owned")
        )

        # Bottom buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill="x", padx=20, pady=10)

        delete_button = tk.Button(
            bottom_frame,
            text="Delete Selected",
            command=self._delete_selected
        )
        delete_button.pack(side="left")

        quit_button = tk.Button(
            bottom_frame,
            text="Quit",
            command=self.quit
        )
        quit_button.pack(side="right")

    def _create_menu(self):
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add Game", command=self._add_game)
        file_menu.add_command(label="Discover IGDB", command=self._discover_games)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

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
        messagebox.showinfo("IGDB Discovery", "This will search the IGDB API later.")

    def _delete_selected(self):
        selected_item = self.game_table.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a game first.")
            return

        confirm = messagebox.askyesno(
            "Delete Game",
            "Are you sure you want to delete the selected game?"
        )

        if confirm:
            self.game_table.delete(selected_item)

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "DS ROM Library\nA prototype for organizing Nintendo DS ROMs."
        )

    def _show_help(self):
        messagebox.showinfo(
            "Help",
            "Use the search bar to find games.\nUse Add Game to save a ROM entry.\nUse Discover IGDB to search game metadata."
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()