"""Shared visual theme for the RomDex desktop application."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


class Colors:
    """Central color palette used across RomDex."""

    BACKGROUND = "#0D1117"
    SIDEBAR = "#10151D"
    SURFACE = "#161C25"
    SURFACE_ALT = "#1D2531"
    SURFACE_HOVER = "#263140"
    BORDER = "#2C3746"

    TEXT = "#F4F7FB"
    TEXT_SECONDARY = "#A8B3C2"
    TEXT_MUTED = "#778394"

    ACCENT = "#7C5CFC"
    ACCENT_HOVER = "#8D72FF"
    ACCENT_PRESSED = "#6847E8"
    ACCENT_SOFT = "#282246"

    SUCCESS = "#49C98A"
    WARNING = "#F4BE5B"
    DANGER = "#F06B78"
    DANGER_HOVER = "#FF7E8A"

    SELECTION = "#322A59"


class Fonts:
    """Font families and sizes used by the application."""

    FAMILY = "Segoe UI"
    MONO = "Cascadia Mono"

    BODY = (FAMILY, 10)
    BODY_BOLD = (FAMILY, 10, "bold")
    SMALL = (FAMILY, 9)
    SMALL_BOLD = (FAMILY, 9, "bold")
    TITLE = (FAMILY, 23, "bold")
    PAGE_TITLE = (FAMILY, 20, "bold")
    SECTION_TITLE = (FAMILY, 12, "bold")
    BRAND = (FAMILY, 18, "bold")


def _configure_named_fonts(root: tk.Misc) -> None:
    """Update Tk's named fonts so legacy widgets match the theme."""

    named_fonts = {
        "TkDefaultFont": (Fonts.FAMILY, 10),
        "TkTextFont": (Fonts.FAMILY, 10),
        "TkMenuFont": (Fonts.FAMILY, 10),
        "TkHeadingFont": (Fonts.FAMILY, 10, "bold"),
        "TkCaptionFont": (Fonts.FAMILY, 10, "bold"),
        "TkSmallCaptionFont": (Fonts.FAMILY, 9),
        "TkIconFont": (Fonts.FAMILY, 10),
        "TkTooltipFont": (Fonts.FAMILY, 9),
    }

    for name, font_settings in named_fonts.items():
        try:
            tkfont.nametofont(name, root=root).configure(
                family=font_settings[0],
                size=font_settings[1],
                weight=(
                    font_settings[2]
                    if len(font_settings) > 2
                    else "normal"
                ),
            )
        except tk.TclError:
            continue


def apply_theme(root: tk.Misc) -> ttk.Style:
    """Apply the complete RomDex theme and return the ttk style object."""

    _configure_named_fonts(root)

    style = ttk.Style(root)

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    try:
        root.configure(background=Colors.BACKGROUND)
    except tk.TclError:
        pass

    # Native Tk option defaults.
    root.option_add("*Background", Colors.BACKGROUND)
    root.option_add("*Foreground", Colors.TEXT)
    root.option_add("*selectBackground", Colors.ACCENT)
    root.option_add("*selectForeground", Colors.TEXT)
    root.option_add("*insertBackground", Colors.TEXT)
    root.option_add("*Menu.background", Colors.SURFACE)
    root.option_add("*Menu.foreground", Colors.TEXT)
    root.option_add("*Menu.activeBackground", Colors.ACCENT)
    root.option_add("*Menu.activeForeground", Colors.TEXT)
    root.option_add("*Menu.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.background", Colors.SURFACE_ALT)
    root.option_add("*TCombobox*Listbox.foreground", Colors.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", Colors.ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", Colors.TEXT)

    # Frames and surfaces.
    style.configure("TFrame", background=Colors.BACKGROUND)
    style.configure("App.TFrame", background=Colors.BACKGROUND)
    style.configure("Sidebar.TFrame", background=Colors.SIDEBAR)
    style.configure("Surface.TFrame", background=Colors.SURFACE)
    style.configure("Card.TFrame", background=Colors.SURFACE)
    style.configure("PageHeader.TFrame", background=Colors.BACKGROUND)
    style.configure("Footer.TFrame", background=Colors.BACKGROUND)

    # Labels.
    style.configure(
        "TLabel",
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT,
        font=Fonts.BODY,
    )
    style.configure(
        "Surface.TLabel",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        font=Fonts.BODY,
    )
    style.configure(
        "Title.TLabel",
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT,
        font=Fonts.TITLE,
    )
    style.configure(
        "PageTitle.TLabel",
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT,
        font=Fonts.PAGE_TITLE,
    )
    style.configure(
        "Subtitle.TLabel",
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT_SECONDARY,
        font=Fonts.BODY,
    )
    style.configure(
        "SectionTitle.TLabel",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        font=Fonts.SECTION_TITLE,
    )
    style.configure(
        "Muted.TLabel",
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT_MUTED,
        font=Fonts.SMALL,
    )
    style.configure(
        "SidebarMuted.TLabel",
        background=Colors.SIDEBAR,
        foreground=Colors.TEXT_MUTED,
        font=Fonts.SMALL,
    )
    style.configure(
        "SidebarStatus.TLabel",
        background=Colors.SIDEBAR,
        foreground=Colors.TEXT_SECONDARY,
        font=Fonts.SMALL,
    )
    style.configure(
        "Brand.TLabel",
        background=Colors.SIDEBAR,
        foreground=Colors.TEXT,
        font=Fonts.BRAND,
    )
    style.configure(
        "BrandSubtitle.TLabel",
        background=Colors.SIDEBAR,
        foreground=Colors.TEXT_MUTED,
        font=(Fonts.FAMILY, 8, "bold"),
    )

    # Standard buttons.
    style.configure(
        "TButton",
        background=Colors.SURFACE_ALT,
        foreground=Colors.TEXT,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.SURFACE_ALT,
        darkcolor=Colors.SURFACE_ALT,
        padding=(14, 9),
        font=Fonts.BODY_BOLD,
        relief="flat",
    )
    style.map(
        "TButton",
        background=[
            ("disabled", Colors.SURFACE),
            ("pressed", Colors.SURFACE_HOVER),
            ("active", Colors.SURFACE_HOVER),
        ],
        foreground=[
            ("disabled", Colors.TEXT_MUTED),
            ("active", Colors.TEXT),
        ],
        bordercolor=[
            ("focus", Colors.ACCENT),
            ("active", Colors.ACCENT),
        ],
    )

    style.configure(
        "Accent.TButton",
        background=Colors.ACCENT,
        foreground="#FFFFFF",
        bordercolor=Colors.ACCENT,
        lightcolor=Colors.ACCENT,
        darkcolor=Colors.ACCENT,
        padding=(16, 10),
        font=Fonts.BODY_BOLD,
        relief="flat",
    )
    style.map(
        "Accent.TButton",
        background=[
            ("disabled", Colors.SURFACE_HOVER),
            ("pressed", Colors.ACCENT_PRESSED),
            ("active", Colors.ACCENT_HOVER),
        ],
        foreground=[("disabled", Colors.TEXT_MUTED)],
        bordercolor=[
            ("pressed", Colors.ACCENT_PRESSED),
            ("active", Colors.ACCENT_HOVER),
        ],
    )

    style.configure(
        "Secondary.TButton",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.SURFACE,
        darkcolor=Colors.SURFACE,
        padding=(14, 9),
        font=Fonts.BODY_BOLD,
        relief="flat",
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("pressed", Colors.SURFACE_ALT),
            ("active", Colors.SURFACE_HOVER),
        ],
        bordercolor=[
            ("focus", Colors.ACCENT),
            ("active", Colors.ACCENT),
        ],
    )

    style.configure(
        "Danger.TButton",
        background=Colors.SURFACE,
        foreground=Colors.DANGER,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.SURFACE,
        darkcolor=Colors.SURFACE,
        padding=(14, 9),
        font=Fonts.BODY_BOLD,
        relief="flat",
    )
    style.map(
        "Danger.TButton",
        background=[
            ("pressed", Colors.SURFACE_ALT),
            ("active", Colors.SURFACE_HOVER),
        ],
        foreground=[("active", Colors.DANGER_HOVER)],
        bordercolor=[("active", Colors.DANGER)],
    )

    # Sidebar navigation.
    style.configure(
        "Nav.TButton",
        background=Colors.SIDEBAR,
        foreground=Colors.TEXT_SECONDARY,
        bordercolor=Colors.SIDEBAR,
        lightcolor=Colors.SIDEBAR,
        darkcolor=Colors.SIDEBAR,
        padding=(16, 12),
        font=Fonts.BODY_BOLD,
        anchor="w",
        relief="flat",
    )
    style.map(
        "Nav.TButton",
        background=[
            ("pressed", Colors.SURFACE_ALT),
            ("active", Colors.SURFACE_ALT),
        ],
        foreground=[("active", Colors.TEXT)],
        bordercolor=[
            ("pressed", Colors.SURFACE_ALT),
            ("active", Colors.SURFACE_ALT),
        ],
    )

    style.configure(
        "NavActive.TButton",
        background=Colors.ACCENT_SOFT,
        foreground=Colors.TEXT,
        bordercolor=Colors.ACCENT_SOFT,
        lightcolor=Colors.ACCENT_SOFT,
        darkcolor=Colors.ACCENT_SOFT,
        padding=(16, 12),
        font=Fonts.BODY_BOLD,
        anchor="w",
        relief="flat",
    )
    style.map(
        "NavActive.TButton",
        background=[
            ("pressed", Colors.ACCENT_SOFT),
            ("active", Colors.ACCENT_SOFT),
        ],
        foreground=[("active", Colors.TEXT)],
        bordercolor=[
            ("pressed", Colors.ACCENT_SOFT),
            ("active", Colors.ACCENT_SOFT),
        ],
    )

    # Inputs.
    style.configure(
        "TEntry",
        fieldbackground=Colors.SURFACE_ALT,
        foreground=Colors.TEXT,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.BORDER,
        darkcolor=Colors.BORDER,
        insertcolor=Colors.TEXT,
        padding=(11, 9),
        relief="flat",
    )
    style.map(
        "TEntry",
        bordercolor=[
            ("focus", Colors.ACCENT),
            ("active", Colors.ACCENT),
        ],
        lightcolor=[("focus", Colors.ACCENT)],
        darkcolor=[("focus", Colors.ACCENT)],
    )

    style.configure(
        "TCombobox",
        fieldbackground=Colors.SURFACE_ALT,
        background=Colors.SURFACE_ALT,
        foreground=Colors.TEXT,
        arrowcolor=Colors.TEXT_SECONDARY,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.BORDER,
        darkcolor=Colors.BORDER,
        padding=(10, 8),
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", Colors.SURFACE_ALT),
            ("focus", Colors.SURFACE_ALT),
        ],
        foreground=[
            ("readonly", Colors.TEXT),
            ("focus", Colors.TEXT),
        ],
        background=[
            ("readonly", Colors.SURFACE_ALT),
            ("active", Colors.SURFACE_HOVER),
        ],
        bordercolor=[("focus", Colors.ACCENT)],
        arrowcolor=[("active", Colors.TEXT)],
    )

    # Checkbuttons and radiobuttons.
    for widget_style in ("TCheckbutton", "TRadiobutton"):
        style.configure(
            widget_style,
            background=Colors.BACKGROUND,
            foreground=Colors.TEXT_SECONDARY,
            font=Fonts.BODY,
        )
        style.map(
            widget_style,
            background=[("active", Colors.BACKGROUND)],
            foreground=[("active", Colors.TEXT)],
            indicatorcolor=[
                ("selected", Colors.ACCENT),
                ("!selected", Colors.SURFACE_ALT),
            ],
        )

    # Tables.
    style.configure(
        "Treeview",
        background=Colors.SURFACE,
        fieldbackground=Colors.SURFACE,
        foreground=Colors.TEXT_SECONDARY,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.SURFACE,
        darkcolor=Colors.SURFACE,
        rowheight=36,
        font=Fonts.BODY,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", Colors.SELECTION)],
        foreground=[("selected", Colors.TEXT)],
    )
    style.configure(
        "Treeview.Heading",
        background=Colors.SURFACE_ALT,
        foreground=Colors.TEXT,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.SURFACE_ALT,
        darkcolor=Colors.SURFACE_ALT,
        padding=(10, 10),
        font=Fonts.SMALL_BOLD,
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", Colors.SURFACE_HOVER)],
        foreground=[("active", Colors.TEXT)],
    )

    # Label frames become card-like sections.
    style.configure(
        "TLabelframe",
        background=Colors.SURFACE,
        bordercolor=Colors.BORDER,
        lightcolor=Colors.BORDER,
        darkcolor=Colors.BORDER,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=Colors.SURFACE,
        foreground=Colors.TEXT,
        font=Fonts.SECTION_TITLE,
        padding=(4, 2),
    )

    # Scrollbars and separators.
    style.configure(
        "Vertical.TScrollbar",
        background=Colors.SURFACE_ALT,
        troughcolor=Colors.BACKGROUND,
        bordercolor=Colors.BACKGROUND,
        arrowcolor=Colors.TEXT_MUTED,
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", Colors.SURFACE_HOVER)],
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=Colors.SURFACE_ALT,
        troughcolor=Colors.BACKGROUND,
        bordercolor=Colors.BACKGROUND,
        arrowcolor=Colors.TEXT_MUTED,
        relief="flat",
    )
    style.map(
        "Horizontal.TScrollbar",
        background=[("active", Colors.SURFACE_HOVER)],
    )
    style.configure(
        "TSeparator",
        background=Colors.BORDER,
    )

    # Progress bar used by the launch animation.
    style.configure(
        "Horizontal.TProgressbar",
        background=Colors.ACCENT,
        troughcolor=Colors.SURFACE_ALT,
        bordercolor=Colors.SURFACE_ALT,
        lightcolor=Colors.ACCENT,
        darkcolor=Colors.ACCENT,
        thickness=8,
    )

    # Retained for any older Notebook widgets used elsewhere.
    style.configure(
        "TNotebook",
        background=Colors.BACKGROUND,
        borderwidth=0,
        tabmargins=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=Colors.SURFACE,
        foreground=Colors.TEXT_SECONDARY,
        padding=(18, 10),
        font=Fonts.BODY_BOLD,
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", Colors.ACCENT_SOFT),
            ("active", Colors.SURFACE_HOVER),
        ],
        foreground=[
            ("selected", Colors.TEXT),
            ("active", Colors.TEXT),
        ],
    )

    return style


def style_legacy_widgets(root: tk.Misc) -> None:
    """Style standard Tk widgets that do not use ttk.Style."""

    try:
        children = root.winfo_children()
    except tk.TclError:
        return

    for widget in children:
        try:
            if isinstance(widget, tk.Text):
                widget.configure(
                    background=Colors.SURFACE,
                    foreground=Colors.TEXT_SECONDARY,
                    insertbackground=Colors.TEXT,
                    selectbackground=Colors.ACCENT,
                    selectforeground="#FFFFFF",
                    highlightbackground=Colors.BORDER,
                    highlightcolor=Colors.ACCENT,
                    highlightthickness=1,
                    borderwidth=0,
                    relief="flat",
                    padx=14,
                    pady=12,
                    font=Fonts.BODY,
                )
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    background=Colors.SURFACE_ALT,
                    foreground=Colors.TEXT,
                    insertbackground=Colors.TEXT,
                    selectbackground=Colors.ACCENT,
                    selectforeground="#FFFFFF",
                    highlightbackground=Colors.BORDER,
                    highlightcolor=Colors.ACCENT,
                    highlightthickness=1,
                    borderwidth=0,
                    relief="flat",
                    font=Fonts.BODY,
                )
            elif isinstance(widget, tk.Listbox):
                widget.configure(
                    background=Colors.SURFACE,
                    foreground=Colors.TEXT_SECONDARY,
                    selectbackground=Colors.SELECTION,
                    selectforeground=Colors.TEXT,
                    highlightbackground=Colors.BORDER,
                    highlightcolor=Colors.ACCENT,
                    highlightthickness=1,
                    borderwidth=0,
                    relief="flat",
                    font=Fonts.BODY,
                )
        except tk.TclError:
            pass

        style_legacy_widgets(widget)
