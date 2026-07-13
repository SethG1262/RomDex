"""Modern left-side navigation for RomDex."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ui.theme import Colors, Fonts


class NavigationSidebar(ttk.Frame):
    """Persistent navigation and high-value quick actions."""

    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None],
        on_add_rom: Callable[[], None],
        on_emulator_settings: Callable[[], None],
        on_help: Callable[[], None],
    ):
        super().__init__(
            parent,
            style="Sidebar.TFrame",
            width=238,
        )

        self.on_navigate = on_navigate
        self._navigation_buttons: dict[str, ttk.Button] = {}
        self._active_page: str | None = None

        self.grid_propagate(False)
        self.pack_propagate(False)

        self._build_brand()
        self._build_navigation()
        self._build_spacer()
        self._build_quick_actions(
            on_add_rom=on_add_rom,
            on_emulator_settings=on_emulator_settings,
            on_help=on_help,
        )

    def _build_brand(self) -> None:
        brand_frame = ttk.Frame(self, style="Sidebar.TFrame")
        brand_frame.pack(fill="x", padx=20, pady=(22, 28))

        logo = tk.Label(
            brand_frame,
            text="R",
            width=2,
            height=1,
            background=Colors.ACCENT,
            foreground="#FFFFFF",
            font=(Fonts.FAMILY, 16, "bold"),
            borderwidth=0,
            relief="flat",
        )
        logo.pack(side="left", padx=(0, 12))

        text_frame = ttk.Frame(brand_frame, style="Sidebar.TFrame")
        text_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(
            text_frame,
            text="RomDex",
            style="Brand.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            text_frame,
            text="LIBRARY MANAGER",
            style="BrandSubtitle.TLabel",
        ).pack(anchor="w", pady=(1, 0))

    def _build_navigation(self) -> None:
        navigation_frame = ttk.Frame(self, style="Sidebar.TFrame")
        navigation_frame.pack(fill="x", padx=14)

        ttk.Label(
            navigation_frame,
            text="NAVIGATION",
            style="SidebarMuted.TLabel",
        ).pack(anchor="w", padx=8, pady=(0, 8))

        items = (
            ("library", "▦   Library"),
            ("discover", "⌕   Discover"),
            ("cloud", "☁   Cloud Library"),
        )

        for key, label in items:
            button = ttk.Button(
                navigation_frame,
                text=label,
                style="Nav.TButton",
                command=lambda page_key=key: self.on_navigate(page_key),
            )
            button.pack(fill="x", pady=3)
            self._navigation_buttons[key] = button

    def _build_spacer(self) -> None:
        spacer = ttk.Frame(self, style="Sidebar.TFrame")
        spacer.pack(fill="both", expand=True)

    def _build_quick_actions(
        self,
        *,
        on_add_rom: Callable[[], None],
        on_emulator_settings: Callable[[], None],
        on_help: Callable[[], None],
    ) -> None:
        action_frame = ttk.Frame(self, style="Sidebar.TFrame")
        action_frame.pack(fill="x", padx=14, pady=(0, 18))

        ttk.Separator(action_frame).pack(fill="x", pady=(0, 14))

        ttk.Label(
            action_frame,
            text="QUICK ACTIONS",
            style="SidebarMuted.TLabel",
        ).pack(anchor="w", padx=8, pady=(0, 8))

        ttk.Button(
            action_frame,
            text="＋  Add ROM",
            style="Accent.TButton",
            command=on_add_rom,
        ).pack(fill="x", pady=(0, 7))

        ttk.Button(
            action_frame,
            text="⚙  Emulator settings",
            style="Nav.TButton",
            command=on_emulator_settings,
        ).pack(fill="x", pady=2)

        ttk.Button(
            action_frame,
            text="?   Help & shortcuts",
            style="Nav.TButton",
            command=on_help,
        ).pack(fill="x", pady=2)

        ttk.Label(
            action_frame,
            text="Local-first  •  Private",
            style="SidebarStatus.TLabel",
        ).pack(anchor="w", padx=8, pady=(14, 0))

    def select(self, page_key: str) -> None:
        """Highlight the currently active navigation item."""

        if page_key == self._active_page:
            return

        for key, button in self._navigation_buttons.items():
            button.configure(
                style=(
                    "NavActive.TButton"
                    if key == page_key
                    else "Nav.TButton"
                )
            )

        self._active_page = page_key
