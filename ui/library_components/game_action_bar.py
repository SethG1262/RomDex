import tkinter as tk
from tkinter import ttk


class GameActionBar(ttk.Frame):
    """
    Responsive actions for the selected library game.

    Important actions stay visible. Less-used actions move into a
    More Actions menu when the available width is limited.
    """

    WIDE_LAYOUT_THRESHOLD = 1120

    def __init__(
        self,
        parent,
        on_play,
        on_configure_emulator,
        on_attach_rom,
        on_merge_rom,
        on_detach_rom,
        on_delete,
        on_refresh,
        on_quit,
    ):
        super().__init__(
            parent,
            style="Surface.TFrame",
            padding=(12, 10),
        )

        self.current_game = None
        self.is_launching = False
        self._wide_layout = None

        self._on_merge_rom = on_merge_rom
        self._on_detach_rom = on_detach_rom
        self._on_delete = on_delete
        self._on_refresh = on_refresh
        self._on_quit = on_quit

        self.columnconfigure(5, weight=1)

        self.play_button = ttk.Button(
            self,
            text="▶  Play",
            style="Accent.TButton",
            command=on_play,
        )

        self.configure_button = ttk.Button(
            self,
            text="⚙  Configure Emulator",
            style="Secondary.TButton",
            command=on_configure_emulator,
        )

        self.attach_button = ttk.Button(
            self,
            text="＋  Attach ROM",
            style="Secondary.TButton",
            command=on_attach_rom,
        )

        self.merge_button = ttk.Button(
            self,
            text="Merge Existing ROM",
            style="Secondary.TButton",
            command=on_merge_rom,
        )

        self.detach_button = ttk.Button(
            self,
            text="Detach ROM",
            style="Secondary.TButton",
            command=on_detach_rom,
        )

        self.delete_button = ttk.Button(
            self,
            text="Delete Selected",
            style="Danger.TButton",
            command=on_delete,
        )

        self.refresh_button = ttk.Button(
            self,
            text="↻  Refresh",
            style="Secondary.TButton",
            command=on_refresh,
        )

        self.quit_button = ttk.Button(
            self,
            text="Exit",
            style="Secondary.TButton",
            command=on_quit,
        )

        self.more_button = ttk.Button(
            self,
            text="More Actions  ⋯",
            style="Secondary.TButton",
            command=self._show_more_menu,
        )

        self.more_menu = tk.Menu(self, tearoff=False)
        self._menu_indexes = {
            "merge": 0,
            "detach": 1,
            "delete": 2,
            "refresh": 4,
            "quit": 5,
        }

        self.more_menu.add_command(
            label="Merge Existing ROM",
            command=on_merge_rom,
        )
        self.more_menu.add_command(
            label="Detach ROM",
            command=on_detach_rom,
        )
        self.more_menu.add_command(
            label="Delete Selected",
            command=on_delete,
        )
        self.more_menu.add_separator()
        self.more_menu.add_command(
            label="Refresh Library",
            command=on_refresh,
        )
        self.more_menu.add_command(
            label="Exit RomDex",
            command=on_quit,
        )

        self.bind("<Configure>", self._on_resize)
        self.after_idle(self._apply_responsive_layout)
        self.update_for_game(None)

    def _on_resize(self, event):
        self._apply_responsive_layout(event.width)

    def _apply_responsive_layout(self, available_width=None):
        """Switch between full and compact action layouts."""

        if available_width is None:
            available_width = self.winfo_width()

        use_wide_layout = available_width >= self.WIDE_LAYOUT_THRESHOLD

        if use_wide_layout == self._wide_layout:
            return

        for widget in (
            self.play_button,
            self.configure_button,
            self.attach_button,
            self.merge_button,
            self.detach_button,
            self.delete_button,
            self.refresh_button,
            self.quit_button,
            self.more_button,
        ):
            widget.grid_forget()

        self.play_button.grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.configure_button.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 0),
        )
        self.attach_button.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(8, 0),
        )

        if use_wide_layout:
            self.merge_button.grid(
                row=0,
                column=3,
                sticky="w",
                padx=(8, 0),
            )
            self.detach_button.grid(
                row=0,
                column=4,
                sticky="w",
                padx=(8, 0),
            )
            self.delete_button.grid(
                row=0,
                column=5,
                sticky="w",
                padx=(8, 0),
            )
            self.refresh_button.grid(
                row=0,
                column=6,
                sticky="e",
                padx=(12, 0),
            )
            self.quit_button.grid(
                row=0,
                column=7,
                sticky="e",
                padx=(8, 0),
            )
        else:
            self.more_button.grid(
                row=0,
                column=3,
                sticky="w",
                padx=(8, 0),
            )

        self._wide_layout = use_wide_layout

    def _show_more_menu(self):
        """Open the compact overflow menu under its button."""

        try:
            x = self.more_button.winfo_rootx()
            y = (
                self.more_button.winfo_rooty()
                + self.more_button.winfo_height()
            )
            self.more_menu.tk_popup(x, y)
        finally:
            self.more_menu.grab_release()

    def _set_menu_state(self, action_name, state):
        self.more_menu.entryconfigure(
            self._menu_indexes[action_name],
            state=state,
        )

    def update_for_game(self, game):
        """Update labels and enabled states for the selected game."""

        self.current_game = game

        if self.is_launching:
            return

        if game is None:
            self.play_button.configure(
                text="▶  Play",
                state="disabled",
            )
            self.attach_button.configure(
                text="＋  Attach ROM",
                state="disabled",
            )
            self.merge_button.configure(state="disabled")
            self.detach_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")

            self._set_menu_state("merge", "disabled")
            self._set_menu_state("detach", "disabled")
            self._set_menu_state("delete", "disabled")
            return

        self.delete_button.configure(state="normal")
        self._set_menu_state("delete", "normal")

        self.play_button.configure(
            text="▶  Play",
            state="normal" if game.rom_path else "disabled",
        )

        attach_text = (
            "↺  Replace ROM"
            if game.rom_path
            else "＋  Attach ROM"
        )
        self.attach_button.configure(
            text=attach_text,
            state="normal",
        )

        detach_state = "normal" if game.rom_path else "disabled"
        self.detach_button.configure(state=detach_state)
        self._set_menu_state("detach", detach_state)

        can_merge = bool(
            game.igdb_id is not None
            and not game.rom_path
        )
        merge_state = "normal" if can_merge else "disabled"
        self.merge_button.configure(state=merge_state)
        self._set_menu_state("merge", merge_state)

    def set_launching(self, is_launching):
        """Prevent repeated Play clicks while launch is in progress."""

        self.is_launching = is_launching

        if is_launching:
            self.play_button.configure(
                text="Launching…",
                state="disabled",
            )
            return

        self.update_for_game(self.current_game)
