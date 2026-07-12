from tkinter import ttk


class GameActionBar(ttk.Frame):
    """Actions for the selected library game."""

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
        super().__init__(parent)

        self.current_game = None
        self.is_launching = False

        self.play_button = ttk.Button(
            self,
            text="Play",
            command=on_play,
        )
        self.play_button.pack(side="left")

        self.configure_button = ttk.Button(
            self,
            text="Configure Emulator",
            command=on_configure_emulator,
        )
        self.configure_button.pack(
            side="left",
            padx=(8, 4),
        )

        self.attach_button = ttk.Button(
            self,
            text="Attach ROM",
            command=on_attach_rom,
        )
        self.attach_button.pack(side="left", padx=4)

        self.merge_button = ttk.Button(
            self,
            text="Merge Existing ROM",
            command=on_merge_rom,
        )
        self.merge_button.pack(side="left", padx=4)

        self.detach_button = ttk.Button(
            self,
            text="Detach ROM",
            command=on_detach_rom,
        )
        self.detach_button.pack(side="left", padx=4)

        self.delete_button = ttk.Button(
            self,
            text="Delete Selected",
            command=on_delete,
        )
        self.delete_button.pack(side="left", padx=4)

        ttk.Button(
            self,
            text="Refresh Library",
            command=on_refresh,
        ).pack(side="left", padx=4)

        ttk.Button(
            self,
            text="Quit",
            command=on_quit,
        ).pack(side="right")

        self.update_for_game(None)

    def update_for_game(self, game):
        """
        Updates labels and enabled states for the selected game.
        """
        self.current_game = game

        if self.is_launching:
            return

        if game is None:
            self.play_button.configure(
                text="Play",
                state="disabled",
            )
            self.attach_button.configure(
                text="Attach ROM",
                state="disabled",
            )
            self.merge_button.configure(state="disabled")
            self.detach_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            return

        self.delete_button.configure(state="normal")

        self.play_button.configure(
            text="Play",
            state="normal" if game.rom_path else "disabled",
        )

        self.attach_button.configure(
            text="Replace ROM" if game.rom_path else "Attach ROM",
            state="normal",
        )

        self.detach_button.configure(
            state="normal" if game.rom_path else "disabled"
        )

        can_merge = bool(
            game.igdb_id is not None
            and not game.rom_path
        )
        self.merge_button.configure(
            state="normal" if can_merge else "disabled"
        )

    def set_launching(self, is_launching):
        """
        Prevents repeated Play clicks while the animation is running.
        """
        self.is_launching = is_launching

        if is_launching:
            self.play_button.configure(
                text="Launching...",
                state="disabled",
            )
            return

        self.update_for_game(self.current_game)
