import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
from io import BytesIO
from PIL import Image, ImageTk

from services.db import init_db
from services.library_filter_service import LibraryFilterService

from repositories.game_repository import GameRepository
from ui.discovery_frame import DiscoveryFrame


# Main application window for RomDex.
# This class controls the Tkinter UI, tabs, library table, and user actions.
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Basic window settings
        self.title("RomDex")
        self.geometry("1150x750")
        self.minsize(1000, 650)

        # Repository handles database actions for saved games
        self.game_repository = GameRepository()

        # Service handles library searching, filtering, and sorting
        self.library_filter_service = LibraryFilterService()

        # Keeps a reference to the cover image so Tkinter does not garbage collect it
        self.cover_image = None

        # Build the interface
        self._create_tabs()
        self._create_library_widgets()
        self._create_menu()

        # Load saved games into the library table when the app starts
        self._load_library_games()

    def _create_tabs(self):
        # Notebook creates tabbed navigation
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Library tab shows saved/local games
        self.library_tab = ttk.Frame(self.notebook)

        # Discovery tab handles IGDB game searching
        self.discovery_tab = DiscoveryFrame(self.notebook)

        self.notebook.add(self.library_tab, text="Library")
        self.notebook.add(self.discovery_tab, text="Discover IGDB")

        # Reload the library when the user switches back to the Library tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _create_library_widgets(self):
        # Main title for the library page
        title_label = tk.Label(
            self.library_tab,
            text="DS ROM Library",
            font=("Arial", 22, "bold")
        )
        title_label.pack(pady=15)

        # Top row containing search, add, and discover buttons
        top_frame = tk.Frame(self.library_tab)
        top_frame.pack(fill="x", padx=20)

        self.search_entry = tk.Entry(top_frame, width=40)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "Search games...")
        self.search_entry.bind(
            "<Return>",
            lambda event: self._apply_filters()
        )
        self.search_entry.bind(
            "<FocusIn>",
            self._clear_search_placeholder
        )

        search_button = tk.Button(
            top_frame,
            text="Apply Filters",
            command=self._apply_filters
        )
        search_button.pack(side="left", padx=5)

        reset_button = tk.Button(
            top_frame,
            text="Reset Filters",
            command=self._reset_filters
        )
        reset_button.pack(side="left", padx=5)

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

        # Advanced filter controls
        filter_frame = ttk.LabelFrame(
            self.library_tab,
            text="Advanced Filters",
            padding=10
        )
        filter_frame.pack(fill="x", padx=20, pady=(10, 0))

        ttk.Label(filter_frame, text="Platform:").pack(side="left")

        self.platform_filter = ttk.Combobox(
            filter_frame,
            state="readonly",
            width=18,
            values=["All Platforms"]
        )
        self.platform_filter.set("All Platforms")
        self.platform_filter.pack(side="left", padx=(5, 15))

        ttk.Label(filter_frame, text="Type:").pack(side="left")

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
        self.type_filter.pack(side="left", padx=(5, 15))

        ttk.Label(filter_frame, text="Status:").pack(side="left")

        self.status_filter = ttk.Combobox(
            filter_frame,
            state="readonly",
            width=15,
            values=["All Statuses"]
        )
        self.status_filter.set("All Statuses")
        self.status_filter.pack(side="left", padx=(5, 15))

        ttk.Label(filter_frame, text="Sort:").pack(side="left")

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
        self.sort_filter.pack(side="left", padx=5)

        # Automatically apply filters when a dropdown changes
        self.platform_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self._apply_filters()
        )
        self.type_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self._apply_filters()
        )
        self.status_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self._apply_filters()
        )
        self.sort_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self._apply_filters()
        )

        # Main content area with the game table on the left and details on the right
        content_frame = tk.Frame(self.library_tab)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Columns shown in the Treeview table
        columns = ("title", "platform", "type", "status")

        self.game_table = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings"
        )

        # Table headings
        self.game_table.heading("title", text="Title")
        self.game_table.heading("platform", text="Platform")
        self.game_table.heading("type", text="Type")
        self.game_table.heading("status", text="Status")

        # Table column widths
        self.game_table.column("title", width=300)
        self.game_table.column("platform", width=150)
        self.game_table.column("type", width=140)
        self.game_table.column("status", width=100)

        self.game_table.pack(side="left", fill="both", expand=True)

        # When a game is selected, show its details
        self.game_table.bind("<<TreeviewSelect>>", self._on_library_game_selected)

        # Right-side panel for cover art and game details
        details_frame = tk.Frame(content_frame)
        details_frame.pack(side="right", fill="both", padx=(15, 0))

        details_label = tk.Label(
            details_frame,
            text="Game Info",
            font=("Arial", 12, "bold")
        )
        details_label.pack(anchor="w")

        # Frame used to display the cover image
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

        # Text box for detailed game information
        self.library_details_text = tk.Text(
            details_frame,
            width=45,
            height=12,
            wrap="word"
        )
        self.library_details_text.pack(fill="both", expand=True)

        # Bottom row buttons
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
        # Creates the menu bar at the top of the app
        menu_bar = tk.Menu(self)

        # File menu contains core app actions
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add Game", command=self._add_game)
        file_menu.add_command(label="Discover IGDB", command=self._discover_games)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        menu_bar.add_cascade(label="File", menu=file_menu)

        # Help menu contains basic app information
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Help", command=self._show_help)

        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menu_bar)

    def _clear_search_placeholder(self, event):
        if self.search_entry.get() == "Search games...":
            self.search_entry.delete(0, tk.END)

    def _apply_filters(self):
        # Gets the current filter values from the interface
        search_text = self.search_entry.get().strip()

        if search_text == "Search games...":
            search_text = ""

        games = self.game_repository.get_all_games()

        filtered_games = self.library_filter_service.filter_games(
            games=games,
            search_text=search_text,
            platform=self.platform_filter.get(),
            game_type=self.type_filter.get(),
            status=self.status_filter.get(),
            sort_option=self.sort_filter.get()
        )

        self._display_library_games(filtered_games)

    def _reset_filters(self):
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Search games...")

        self.platform_filter.set("All Platforms")
        self.type_filter.set("All Types")
        self.status_filter.set("All Statuses")
        self.sort_filter.set("Title A-Z")

        self._load_library_games()

    def _refresh_filter_options(self, games):
        platform_options = (
            self.library_filter_service.get_platform_options(games)
        )
        status_options = (
            self.library_filter_service.get_status_options(games)
        )

        current_platform = self.platform_filter.get()
        current_status = self.status_filter.get()

        self.platform_filter["values"] = platform_options
        self.status_filter["values"] = status_options

        if current_platform not in platform_options:
            self.platform_filter.set("All Platforms")

        if current_status not in status_options:
            self.status_filter.set("All Statuses")

    def _add_game(self):
        # Opens a file picker so the user can select one or more .nds files
        rom_paths = filedialog.askopenfilenames(
            title="Select Nintendo DS ROM files",
            filetypes=[
                ("Nintendo DS ROMs", "*.nds"),
                ("All Files", "*.*")
            ]
        )

        # If the user cancels the file picker, stop the method
        if not rom_paths:
            return

        added_count = 0
        skipped_count = 0

        try:
            for rom_path in rom_paths:
                # Only allow .nds files to be added
                if not rom_path.lower().endswith(".nds"):
                    skipped_count += 1
                    continue

                # Prevent duplicate ROM files from being saved
                existing_game = self.game_repository.get_game_by_rom_path(rom_path)

                if existing_game:
                    skipped_count += 1
                    continue

                # Save the local ROM information into the database
                self.game_repository.add_local_rom(rom_path)
                added_count += 1

            # Refresh the table after adding games
            self._load_library_games()

            messagebox.showinfo(
                "Add Game Complete",
                f"Added {added_count} game file(s).\n"
                f"Skipped {skipped_count} file(s)."
            )

        except Exception as error:
            # Shows the error instead of crashing the program
            messagebox.showerror("Add Game Error", str(error))

    def _discover_games(self):
        # Switches the app to the IGDB discovery tab
        self.notebook.select(self.discovery_tab)

    def _on_tab_changed(self, event):
        # Detects which tab is currently selected
        selected_tab = self.notebook.select()

        # If the user returns to the Library tab, reload the saved games
        if selected_tab == str(self.library_tab):
            self._load_library_games()

    def _on_library_game_selected(self, event):
        # Gets the selected row from the library table
        selected_item = self.game_table.selection()

        if not selected_item:
            return

        # The Treeview item id is stored as the game database id
        game_id = int(selected_item[0])
        game = self.game_repository.get_game_by_id(game_id)

        if not game:
            return

        # Checks whether the game has a local ROM file and/or IGDB metadata
        has_local_rom = bool(game.rom_path)
        has_igdb_metadata = bool(game.igdb_id)

        # Load cover art if the game has a cover URL
        if game.cover_url:
            self.cover_frame.pack(pady=(5, 10))
            self._load_cover_art(game.cover_url)
        else:
            self.cover_frame.pack_forget()
            self.cover_image = None

        # Determines what kind of saved game entry this is
        if has_local_rom and has_igdb_metadata:
            game_type = "Local ROM + IGDB Metadata"
        elif has_local_rom:
            game_type = "Local ROM Only"
        elif has_igdb_metadata:
            game_type = "IGDB Metadata Only"
        else:
            game_type = "Manual Entry"

        # Builds the details text shown on the right panel
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

        # Updates the details text box
        self.library_details_text.delete("1.0", tk.END)
        self.library_details_text.insert(tk.END, details)

    def _get_large_cover_url(self, cover_url):
        # Converts smaller IGDB cover image URLs into larger versions when possible
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
        # Downloads and displays cover art from IGDB
        if not cover_url:
            self.cover_frame.pack_forget()
            self.cover_image = None
            return

        try:
            # Try to use a larger cover image for better quality
            large_cover_url = self._get_large_cover_url(cover_url)

            # Download the cover image
            response = requests.get(large_cover_url, timeout=10)
            response.raise_for_status()

            # Convert the downloaded bytes into an image
            image_data = BytesIO(response.content)
            image = Image.open(image_data)

            # Resize image to fit the cover frame
            image = image.resize((260, 360), Image.LANCZOS)

            # Convert image for Tkinter display
            self.cover_image = ImageTk.PhotoImage(image)

            self.cover_label.config(
                image=self.cover_image,
                text=""
            )

        except Exception as error:
            # If cover loading fails, show an error message inside the cover area
            self.cover_label.config(
                image="",
                text=f"Cover failed to load\n{error}"
            )
            self.cover_image = None

    def _delete_selected(self):
        # Gets the selected game from the table
        selected_item = self.game_table.selection()

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a game first.")
            return

        # Ask for confirmation before deleting
        confirm = messagebox.askyesno(
            "Delete Game",
            "Are you sure you want to delete the selected game?"
        )

        if not confirm:
            return

        game_id = int(selected_item[0])

        try:
            # Delete the selected game from the database
            self.game_repository.delete_game(game_id)

            # Refresh the library after deletion
            self._load_library_games()

        except Exception as error:
            messagebox.showerror("Delete Error", str(error))

    def _display_library_games(self, games):
        # Clears all current rows from the table
        for row in self.game_table.get_children():
            self.game_table.delete(row)

        # Clears the details panel if it already exists
        if hasattr(self, "library_details_text"):
            self.library_details_text.delete("1.0", tk.END)

        # Hides the cover frame until a game with cover art is selected
        if hasattr(self, "cover_frame"):
            self.cover_frame.pack_forget()
            self.cover_image = None

        for game in games:
            game_type = self.library_filter_service.get_game_type(game)

            # Adds the game as a row in the table
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

    def _load_library_games(self):
        # Gets all games from the database
        games = self.game_repository.get_all_games()

        # Updates dropdown options from actual saved data
        self._refresh_filter_options(games)

        # Displays the full library using the default sort
        filtered_games = self.library_filter_service.filter_games(
            games=games,
            sort_option="Title A-Z"
        )
        self._display_library_games(filtered_games)

    def _show_about(self):
        # Shows basic app information
        messagebox.showinfo(
            "About",
            "RomDex\nA prototype for organizing Nintendo DS, DSi, and 3DS games."
        )

    def _show_help(self):
        # Shows simple instructions for using the app
        messagebox.showinfo(
            "Help",
            "Use the Library tab to view saved games.\n"
            "Use Add Game to add local .nds files.\n"
            "Use the advanced filters to narrow and sort the library.\n"
            "Use the Discover IGDB tab to search game metadata."
        )

    def _on_close(self):
        # Safely closes the discovery tab if it has resources to clean up
        try:
            self.discovery_tab.close()
        except Exception:
            pass

        # Safely closes the database/repository connection
        try:
            self.game_repository.close()
        except Exception:
            pass

        # Closes the Tkinter window
        self.destroy()


# Runs only when this file is executed directly
if __name__ == "__main__":
    # Creates database tables if they do not already exist
    init_db()

    # Starts the RomDex desktop application
    app = App()
    app.mainloop()
