import tkinter as tk
from tkinter import ttk


class LibraryFilterBar(ttk.LabelFrame):
    """Advanced filtering and sorting controls."""

    TYPE_OPTIONS = (
        "All Types",
        "Local ROM",
        "IGDB",
        "Local + IGDB",
        "Manual",
    )

    SORT_OPTIONS = (
        "Title A-Z",
        "Title Z-A",
        "Newest Added",
        "Oldest Added",
    )

    def __init__(self, parent, on_filters_changed):
        super().__init__(
            parent,
            text="Advanced Filters",
            padding=10,
        )

        self.on_filters_changed = on_filters_changed

        self.platform_var = tk.StringVar(value="All Platforms")
        self.type_var = tk.StringVar(value="All Types")
        self.status_var = tk.StringVar(value="All Statuses")
        self.sort_var = tk.StringVar(value="Title A-Z")

        self._create_widgets()

    def _create_widgets(self):
        self.platform_filter = self._add_combobox(
            label="Platform:",
            variable=self.platform_var,
            values=("All Platforms",),
            width=18,
        )

        self.type_filter = self._add_combobox(
            label="Type:",
            variable=self.type_var,
            values=self.TYPE_OPTIONS,
            width=15,
        )

        self.status_filter = self._add_combobox(
            label="Status:",
            variable=self.status_var,
            values=("All Statuses",),
            width=15,
        )

        self.sort_filter = self._add_combobox(
            label="Sort:",
            variable=self.sort_var,
            values=self.SORT_OPTIONS,
            width=15,
            final=True,
        )

    def _add_combobox(
        self,
        label,
        variable,
        values,
        width,
        final=False,
    ):
        ttk.Label(self, text=label).pack(side="left")

        combobox = ttk.Combobox(
            self,
            textvariable=variable,
            state="readonly",
            width=width,
            values=values,
        )
        combobox.pack(
            side="left",
            padx=(5, 5 if final else 15),
        )
        combobox.bind(
            "<<ComboboxSelected>>",
            lambda event: self.on_filters_changed(),
        )

        return combobox

    def get_filters(self):
        return {
            "platform": self.platform_var.get(),
            "game_type": self.type_var.get(),
            "status": self.status_var.get(),
            "sort_option": self.sort_var.get(),
        }

    def reset(self):
        self.platform_var.set("All Platforms")
        self.type_var.set("All Types")
        self.status_var.set("All Statuses")
        self.sort_var.set("Title A-Z")

    def update_options(
        self,
        platform_options,
        status_options,
    ):
        current_platform = self.platform_var.get()
        current_status = self.status_var.get()

        self.platform_filter["values"] = platform_options
        self.status_filter["values"] = status_options

        if current_platform not in platform_options:
            self.platform_var.set("All Platforms")

        if current_status not in status_options:
            self.status_var.set("All Statuses")
