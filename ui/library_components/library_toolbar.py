import tkinter as tk
from tkinter import ttk


class LibraryToolbar(ttk.Frame):
    """Search and primary navigation controls for the library tab."""

    SEARCH_PLACEHOLDER = "Search games..."

    def __init__(
        self,
        parent,
        on_search_changed,
        on_apply_filters,
        on_reset_filters,
        on_add_game,
        on_discover,
    ):
        super().__init__(parent)

        self.on_search_changed = on_search_changed
        self.search_var = tk.StringVar(
            value=self.SEARCH_PLACEHOLDER
        )

        self.search_entry = ttk.Entry(
            self,
            textvariable=self.search_var,
            width=40,
        )
        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
        )
        self.search_entry.bind(
            "<KeyRelease>",
            lambda event: self.on_search_changed(),
        )
        self.search_entry.bind(
            "<FocusIn>",
            self._clear_placeholder,
        )
        self.search_entry.bind(
            "<FocusOut>",
            self._restore_placeholder,
        )

        ttk.Button(
            self,
            text="Apply Filters",
            command=on_apply_filters,
        ).pack(side="left", padx=5)

        ttk.Button(
            self,
            text="Reset Filters",
            command=on_reset_filters,
        ).pack(side="left", padx=5)

        ttk.Button(
            self,
            text="Add Game",
            command=on_add_game,
        ).pack(side="left", padx=5)

        ttk.Button(
            self,
            text="Discover IGDB",
            command=on_discover,
        ).pack(side="left", padx=5)

    def get_search_text(self):
        search_text = self.search_var.get().strip()

        if search_text == self.SEARCH_PLACEHOLDER:
            return ""

        return search_text

    def reset_search(self):
        self.search_var.set(self.SEARCH_PLACEHOLDER)

    def _clear_placeholder(self, event=None):
        if self.search_var.get() == self.SEARCH_PLACEHOLDER:
            self.search_var.set("")

    def _restore_placeholder(self, event=None):
        if not self.search_var.get().strip():
            self.search_var.set(self.SEARCH_PLACEHOLDER)
