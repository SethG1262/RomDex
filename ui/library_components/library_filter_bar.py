"""Modern, responsive advanced filters for the RomDex Library page."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


try:
    # Uses the shared theme from the RomDex modern UI package.
    from ui.theme import Colors, Fonts
except ImportError:
    # Safe fallback so the component still works by itself.
    class Colors:
        BACKGROUND = "#0D1117"
        SURFACE = "#161C25"
        SURFACE_ALT = "#1D2531"
        SURFACE_HOVER = "#263140"
        BORDER = "#2C3746"
        TEXT = "#F4F7FB"
        TEXT_SECONDARY = "#A8B3C2"
        TEXT_MUTED = "#778394"
        ACCENT = "#7C5CFC"
        ACCENT_HOVER = "#8D72FF"
        ACCENT_SOFT = "#282246"

    class Fonts:
        FAMILY = "Segoe UI"
        BODY = (FAMILY, 10)
        BODY_BOLD = (FAMILY, 10, "bold")
        SMALL = (FAMILY, 9)
        SMALL_BOLD = (FAMILY, 9, "bold")
        SECTION_TITLE = (FAMILY, 12, "bold")


class LibraryFilterBar(ttk.Frame):
    """
    Responsive advanced filtering and sorting controls.

    Public methods intentionally match the original component:
    - get_filters()
    - reset()
    - update_options()

    This allows LibraryFrame to keep using the component without
    changing repository, filtering, or database logic.
    """

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

    DEFAULTS = {
        "platform": "All Platforms",
        "game_type": "All Types",
        "status": "All Statuses",
        "sort_option": "Title A-Z",
    }

    # Responsive breakpoints for four, two, or one field per row.
    FOUR_COLUMN_WIDTH = 860
    TWO_COLUMN_WIDTH = 520

    def __init__(
        self,
        parent,
        on_filters_changed: Callable[[], None],
    ):
        self._configure_styles(parent)

        super().__init__(
            parent,
            style="FilterCard.TFrame",
            padding=(16, 14),
        )

        self.on_filters_changed = on_filters_changed
        self._expanded = True
        self._current_column_count: int | None = None
        self._resize_job: str | None = None

        self.platform_var = tk.StringVar(
            value=self.DEFAULTS["platform"]
        )
        self.type_var = tk.StringVar(
            value=self.DEFAULTS["game_type"]
        )
        self.status_var = tk.StringVar(
            value=self.DEFAULTS["status"]
        )
        self.sort_var = tk.StringVar(
            value=self.DEFAULTS["sort_option"]
        )

        self._field_frames: list[ttk.Frame] = []
        self._chip_widgets: list[tk.Label] = []

        self.columnconfigure(0, weight=1)

        self._create_header()
        self._create_filter_body()
        self._create_active_filter_row()

        self.bind("<Configure>", self._schedule_responsive_layout)
        self.after_idle(self._finish_setup)

    # ---------------------------------------------------------
    # Visual setup
    # ---------------------------------------------------------

    @staticmethod
    def _configure_styles(parent) -> None:
        """Create styles specific to the modern filter card."""

        style = ttk.Style(parent)

        style.configure(
            "FilterCard.TFrame",
            background=Colors.SURFACE,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BORDER,
            darkcolor=Colors.BORDER,
            borderwidth=1,
            relief="solid",
        )

        style.configure(
            "FilterHeader.TFrame",
            background=Colors.SURFACE,
        )

        style.configure(
            "FilterBody.TFrame",
            background=Colors.SURFACE,
        )

        style.configure(
            "FilterField.TFrame",
            background=Colors.SURFACE,
        )

        style.configure(
            "FilterTitle.TLabel",
            background=Colors.SURFACE,
            foreground=Colors.TEXT,
            font=Fonts.SECTION_TITLE,
        )

        style.configure(
            "FilterSubtitle.TLabel",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_MUTED,
            font=Fonts.SMALL,
        )

        style.configure(
            "FilterFieldLabel.TLabel",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_SECONDARY,
            font=Fonts.SMALL_BOLD,
        )

        style.configure(
            "FilterToggle.TButton",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_SECONDARY,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.SURFACE,
            darkcolor=Colors.SURFACE,
            padding=(11, 7),
            font=Fonts.SMALL_BOLD,
            relief="flat",
        )
        style.map(
            "FilterToggle.TButton",
            background=[
                ("pressed", Colors.SURFACE_ALT),
                ("active", Colors.SURFACE_HOVER),
            ],
            foreground=[("active", Colors.TEXT)],
            bordercolor=[
                ("focus", Colors.ACCENT),
                ("active", Colors.ACCENT),
            ],
        )

        style.configure(
            "FilterReset.TButton",
            background=Colors.SURFACE,
            foreground=Colors.TEXT_SECONDARY,
            bordercolor=Colors.SURFACE,
            lightcolor=Colors.SURFACE,
            darkcolor=Colors.SURFACE,
            padding=(8, 7),
            font=Fonts.SMALL_BOLD,
            relief="flat",
        )
        style.map(
            "FilterReset.TButton",
            background=[
                ("pressed", Colors.SURFACE_ALT),
                ("active", Colors.SURFACE_ALT),
            ],
            foreground=[
                ("disabled", Colors.TEXT_MUTED),
                ("active", Colors.TEXT),
            ],
        )

    def _create_header(self) -> None:
        self.header_frame = ttk.Frame(
            self,
            style="FilterHeader.TFrame",
        )
        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        self.header_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(
            self.header_frame,
            style="FilterHeader.TFrame",
        )
        title_frame.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            title_frame,
            text="Advanced filters",
            style="FilterTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text=(
                "Narrow the library by platform, source, "
                "status, or sorting."
            ),
            style="FilterSubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.active_badge = tk.Label(
            self.header_frame,
            text="No filters active",
            background=Colors.SURFACE_ALT,
            foreground=Colors.TEXT_MUTED,
            font=Fonts.SMALL_BOLD,
            padx=10,
            pady=5,
            borderwidth=0,
        )
        self.active_badge.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(12, 8),
        )

        self.reset_button = ttk.Button(
            self.header_frame,
            text="Reset",
            style="FilterReset.TButton",
            command=self._reset_and_notify,
            state="disabled",
        )
        self.reset_button.grid(
            row=0,
            column=2,
            sticky="e",
            padx=(0, 5),
        )

        self.toggle_button = ttk.Button(
            self.header_frame,
            text="Hide  ▴",
            style="FilterToggle.TButton",
            command=self.toggle_expanded,
        )
        self.toggle_button.grid(
            row=0,
            column=3,
            sticky="e",
        )

    def _create_filter_body(self) -> None:
        self.body_frame = ttk.Frame(
            self,
            style="FilterBody.TFrame",
        )
        self.body_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(14, 0),
        )

        self.platform_filter = self._create_field(
            title="Platform",
            variable=self.platform_var,
            values=("All Platforms",),
        )

        self.type_filter = self._create_field(
            title="Library type",
            variable=self.type_var,
            values=self.TYPE_OPTIONS,
        )

        self.status_filter = self._create_field(
            title="Status",
            variable=self.status_var,
            values=("All Statuses",),
        )

        self.sort_filter = self._create_field(
            title="Sort by",
            variable=self.sort_var,
            values=self.SORT_OPTIONS,
        )

    def _create_field(
        self,
        *,
        title: str,
        variable: tk.StringVar,
        values,
    ) -> ttk.Combobox:
        field_frame = ttk.Frame(
            self.body_frame,
            style="FilterField.TFrame",
        )
        field_frame.columnconfigure(0, weight=1)

        ttk.Label(
            field_frame,
            text=title.upper(),
            style="FilterFieldLabel.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        combobox = ttk.Combobox(
            field_frame,
            textvariable=variable,
            state="readonly",
            values=values,
        )
        combobox.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        combobox.bind(
            "<<ComboboxSelected>>",
            self._on_filter_selected,
        )

        self._field_frames.append(field_frame)
        return combobox

    def _create_active_filter_row(self) -> None:
        self.active_row = ttk.Frame(
            self,
            style="FilterBody.TFrame",
        )
        self.active_row.columnconfigure(1, weight=1)

        ttk.Label(
            self.active_row,
            text="ACTIVE",
            style="FilterFieldLabel.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
        )

        self.chip_frame = ttk.Frame(
            self.active_row,
            style="FilterBody.TFrame",
        )
        self.chip_frame.grid(
            row=0,
            column=1,
            sticky="ew",
        )

    # ---------------------------------------------------------
    # Responsive layout
    # ---------------------------------------------------------

    def _finish_setup(self) -> None:
        self._apply_responsive_layout()
        self._update_active_state()

    def _schedule_responsive_layout(self, _event=None) -> None:
        """
        Debounce resize events so the controls do not visibly flicker
        while the user is dragging the window.
        """

        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except tk.TclError:
                pass

        self._resize_job = self.after(
            40,
            self._apply_responsive_layout,
        )

    def _apply_responsive_layout(self) -> None:
        self._resize_job = None

        width = self.winfo_width()

        if width >= self.FOUR_COLUMN_WIDTH:
            column_count = 4
        elif width >= self.TWO_COLUMN_WIDTH:
            column_count = 2
        else:
            column_count = 1

        if column_count == self._current_column_count:
            return

        for index in range(4):
            self.body_frame.columnconfigure(index, weight=0)

        for field_frame in self._field_frames:
            field_frame.grid_forget()

        for index in range(column_count):
            self.body_frame.columnconfigure(
                index,
                weight=1,
                uniform="library_filter_columns",
            )

        for index, field_frame in enumerate(self._field_frames):
            row = index // column_count
            column = index % column_count

            field_frame.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(
                    0 if column == 0 else 7,
                    0 if column == column_count - 1 else 7,
                ),
                pady=(
                    0 if row == 0 else 12,
                    0,
                ),
            )

        self._current_column_count = column_count

    # ---------------------------------------------------------
    # Filter interaction
    # ---------------------------------------------------------

    def _on_filter_selected(self, _event=None) -> None:
        self._update_active_state()
        self.on_filters_changed()

    def _get_active_filters(self) -> list[tuple[str, str, str]]:
        """
        Return active filters as:
        (internal key, display label, selected value)
        """

        active_filters = []

        values = (
            (
                "platform",
                "Platform",
                self.platform_var.get(),
                self.DEFAULTS["platform"],
            ),
            (
                "game_type",
                "Type",
                self.type_var.get(),
                self.DEFAULTS["game_type"],
            ),
            (
                "status",
                "Status",
                self.status_var.get(),
                self.DEFAULTS["status"],
            ),
            (
                "sort_option",
                "Sort",
                self.sort_var.get(),
                self.DEFAULTS["sort_option"],
            ),
        )

        for key, label, value, default in values:
            if value != default:
                active_filters.append((key, label, value))

        return active_filters

    def _update_active_state(self) -> None:
        active_filters = self._get_active_filters()
        active_count = len(active_filters)

        if active_count == 0:
            self.active_badge.configure(
                text="No filters active",
                background=Colors.SURFACE_ALT,
                foreground=Colors.TEXT_MUTED,
            )
            self.reset_button.configure(state="disabled")
            self.active_row.grid_remove()
        else:
            self.active_badge.configure(
                text=(
                    f"{active_count} active"
                    if active_count != 1
                    else "1 active"
                ),
                background=Colors.ACCENT_SOFT,
                foreground=Colors.TEXT,
            )
            self.reset_button.configure(state="normal")
            self._rebuild_filter_chips(active_filters)

            if self._expanded:
                self.active_row.grid(
                    row=2,
                    column=0,
                    sticky="ew",
                    pady=(12, 0),
                )

    def _rebuild_filter_chips(
        self,
        active_filters: list[tuple[str, str, str]],
    ) -> None:
        for widget in self._chip_widgets:
            widget.destroy()

        self._chip_widgets.clear()

        for index, (key, label, value) in enumerate(active_filters):
            chip = tk.Label(
                self.chip_frame,
                text=f"{label}: {value}  ×",
                background=Colors.ACCENT_SOFT,
                foreground=Colors.TEXT,
                activebackground=Colors.ACCENT_HOVER,
                activeforeground="#FFFFFF",
                font=Fonts.SMALL_BOLD,
                padx=10,
                pady=5,
                cursor="hand2",
                borderwidth=0,
            )
            chip.pack(
                side="left",
                padx=(0 if index == 0 else 6, 0),
            )

            chip.bind(
                "<Button-1>",
                lambda _event, filter_key=key: (
                    self._clear_filter_and_notify(filter_key)
                ),
            )
            chip.bind(
                "<Enter>",
                lambda _event, widget=chip: widget.configure(
                    background=Colors.ACCENT_HOVER,
                ),
            )
            chip.bind(
                "<Leave>",
                lambda _event, widget=chip: widget.configure(
                    background=Colors.ACCENT_SOFT,
                ),
            )

            self._chip_widgets.append(chip)

    def _clear_filter_and_notify(self, filter_key: str) -> None:
        variable_map = {
            "platform": self.platform_var,
            "game_type": self.type_var,
            "status": self.status_var,
            "sort_option": self.sort_var,
        }

        variable = variable_map[filter_key]
        variable.set(self.DEFAULTS[filter_key])

        self._update_active_state()
        self.on_filters_changed()

    def _reset_and_notify(self) -> None:
        self.reset()
        self.on_filters_changed()

    def toggle_expanded(self) -> None:
        self._expanded = not self._expanded

        if self._expanded:
            self.body_frame.grid()
            self.toggle_button.configure(text="Hide  ▴")
            self._apply_responsive_layout()

            if self._get_active_filters():
                self.active_row.grid(
                    row=2,
                    column=0,
                    sticky="ew",
                    pady=(12, 0),
                )
        else:
            self.body_frame.grid_remove()
            self.active_row.grid_remove()
            self.toggle_button.configure(text="Show  ▾")

    # ---------------------------------------------------------
    # Original public API
    # ---------------------------------------------------------

    def get_filters(self) -> dict[str, str]:
        return {
            "platform": self.platform_var.get(),
            "game_type": self.type_var.get(),
            "status": self.status_var.get(),
            "sort_option": self.sort_var.get(),
        }

    def reset(self) -> None:
        """
        Restore the original filter defaults.

        This method intentionally does not call on_filters_changed()
        because LibraryFrame already calls apply_filters after reset().
        """

        self.platform_var.set(self.DEFAULTS["platform"])
        self.type_var.set(self.DEFAULTS["game_type"])
        self.status_var.set(self.DEFAULTS["status"])
        self.sort_var.set(self.DEFAULTS["sort_option"])

        self._update_active_state()

    def update_options(
        self,
        platform_options,
        status_options,
    ) -> None:
        """
        Refresh dynamic platform/status choices while preserving a
        valid current selection.
        """

        platform_options = tuple(platform_options)
        status_options = tuple(status_options)

        current_platform = self.platform_var.get()
        current_status = self.status_var.get()

        self.platform_filter.configure(values=platform_options)
        self.status_filter.configure(values=status_options)

        if current_platform not in platform_options:
            self.platform_var.set(self.DEFAULTS["platform"])

        if current_status not in status_options:
            self.status_var.set(self.DEFAULTS["status"])

        self._update_active_state()
