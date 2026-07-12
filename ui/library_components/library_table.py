from tkinter import ttk


class LibraryTable(ttk.Frame):
    """Scrollable library game table and selection handling."""

    COLUMNS = (
        "title",
        "platform",
        "type",
        "status",
    )

    def __init__(self, parent, on_game_selected):
        super().__init__(parent)

        self.on_game_selected = on_game_selected

        self.tree = ttk.Treeview(
            self,
            columns=self.COLUMNS,
            show="headings",
        )

        headings = {
            "title": "Title",
            "platform": "Platform",
            "type": "Type",
            "status": "Status",
        }
        widths = {
            "title": 300,
            "platform": 150,
            "type": 140,
            "status": 100,
        }

        for column in self.COLUMNS:
            self.tree.heading(
                column,
                text=headings[column],
            )
            self.tree.column(
                column,
                width=widths[column],
            )

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_selection,
        )

    def display_games(self, games, game_type_resolver):
        self.clear()

        for game in games:
            self.tree.insert(
                "",
                "end",
                iid=str(game.id),
                values=(
                    game.title,
                    game.platform or "Unknown",
                    game_type_resolver(game),
                    game.status or "Saved",
                ),
            )

    def get_selected_game_id(self):
        selected_items = self.tree.selection()

        if not selected_items:
            return None

        try:
            return int(selected_items[0])
        except (TypeError, ValueError):
            return None

    def select_game(self, game_id):
        """
        Selects a row by database ID.

        Returns False when the row is not visible under the current
        filters.
        """
        item_id = str(game_id)

        if not self.tree.exists(item_id):
            return False

        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        self.tree.see(item_id)
        self._handle_selection()

        return True

    def clear(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _handle_selection(self, event=None):
        game_id = self.get_selected_game_id()

        if game_id is not None:
            self.on_game_selected(game_id)
