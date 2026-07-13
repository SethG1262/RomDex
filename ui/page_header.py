"""Reusable page heading and action area for RomDex."""

from __future__ import annotations

from tkinter import ttk
from typing import Callable, Iterable


HeaderAction = tuple[str, Callable[[], None], str]


class PageHeader(ttk.Frame):
    """Displays page context and page-specific quick actions."""

    def __init__(self, parent):
        super().__init__(
            parent,
            style="PageHeader.TFrame",
            padding=(28, 22, 28, 18),
        )

        self.columnconfigure(0, weight=1)

        text_frame = ttk.Frame(self, style="PageHeader.TFrame")
        text_frame.grid(row=0, column=0, sticky="w")

        self.title_label = ttk.Label(
            text_frame,
            text="",
            style="PageTitle.TLabel",
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ttk.Label(
            text_frame,
            text="",
            style="Subtitle.TLabel",
        )
        self.subtitle_label.pack(anchor="w", pady=(5, 0))

        self.action_frame = ttk.Frame(
            self,
            style="PageHeader.TFrame",
        )
        self.action_frame.grid(row=0, column=1, sticky="e")

    def set_page(
        self,
        *,
        title: str,
        subtitle: str,
        actions: Iterable[HeaderAction] = (),
    ) -> None:
        """Update the heading and rebuild the action buttons."""

        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)

        for child in self.action_frame.winfo_children():
            child.destroy()

        for index, (label, callback, style_name) in enumerate(actions):
            ttk.Button(
                self.action_frame,
                text=label,
                style=style_name,
                command=callback,
            ).grid(
                row=0,
                column=index,
                padx=(8 if index else 0, 0),
            )
