from tkinter import filedialog, messagebox, ttk

from repositories.game_repository import GameRepository
from services.emulator.emulator_launcher_service import (
    EmulatorLaunchError,
    EmulatorLauncherService,
)
from services.library_filter_service import LibraryFilterService
from ui.emulator_config_dialog import open_emulator_config_dialog
from ui.library_components.game_action_bar import GameActionBar
from ui.library_components.game_details_panel import GameDetailsPanel
from ui.library_components.library_filter_bar import LibraryFilterBar
from ui.library_components.library_table import LibraryTable
from ui.library_components.library_toolbar import LibraryToolbar
from ui.launch_animation_dialog import show_launch_animation
from ui.rom_merge_dialog import show_rom_merge_dialog


class LibraryFrame(ttk.Frame):
    """
    Coordinates the RomDex library tab.

    Widget construction and display logic live in focused components.
    This class handles repository operations and communication between
    those components.
    """

    SUPPORTED_EMULATOR_PLATFORMS = {
        "Nintendo DS",
        "Nintendo DSi",
        "Nintendo 3DS",
    }

    ROM_FILE_TYPES = {
        "Nintendo DS": [
            ("Nintendo DS ROMs", "*.nds"),
            ("All Files", "*.*"),
        ],
        "Nintendo DSi": [
            ("Nintendo DS/DSi ROMs", "*.nds"),
            ("All Files", "*.*"),
        ],
        "Nintendo 3DS": [
            ("Nintendo 3DS ROMs", "*.3ds *.cci *.cxi"),
            ("All Files", "*.*"),
        ],
    }

    def __init__(
        self,
        parent,
        on_discover_requested=None,
        on_quit_requested=None,
    ):
        super().__init__(parent)

        self.on_discover_requested = on_discover_requested
        self.on_quit_requested = on_quit_requested

        self.game_repository = GameRepository()
        self.library_filter_service = LibraryFilterService()
        self.emulator_launcher_service = EmulatorLauncherService()
        self.launch_animation = None

        self._create_widgets()
        self.refresh_library()

    def _create_widgets(self):
        ttk.Label(
            self,
            text="DS ROM Library",
            font=("Arial", 22, "bold"),
        ).pack(pady=15)

        self.toolbar = LibraryToolbar(
            self,
            on_search_changed=self.apply_filters,
            on_apply_filters=self.apply_filters,
            on_reset_filters=self.reset_filters,
            on_add_game=self.add_game,
            on_discover=self._open_discovery,
        )
        self.toolbar.pack(fill="x", padx=20)

        self.filter_bar = LibraryFilterBar(
            self,
            on_filters_changed=self.apply_filters,
        )
        self.filter_bar.pack(fill="x", padx=20, pady=(10, 0))

        content_frame = ttk.Frame(self)
        content_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        self.library_table = LibraryTable(
            content_frame,
            on_game_selected=self._on_game_selected,
        )
        self.library_table.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.details_panel = GameDetailsPanel(content_frame)
        self.details_panel.pack(
            side="right",
            fill="both",
            padx=(15, 0),
        )

        self.action_bar = GameActionBar(
            self,
            on_play=self.play_selected_game,
            on_configure_emulator=self.open_emulator_configuration,
            on_attach_rom=self.attach_or_replace_rom,
            on_merge_rom=self.merge_existing_rom,
            on_detach_rom=self.detach_rom,
            on_delete=self.delete_selected,
            on_refresh=self.refresh_library,
            on_quit=self._quit,
        )
        self.action_bar.pack(fill="x", padx=20, pady=10)

    def apply_filters(self):
        games = self.game_repository.get_all_games()
        filters = self.filter_bar.get_filters()

        filtered_games = self.library_filter_service.filter_games(
            games=games,
            search_text=self.toolbar.get_search_text(),
            platform=filters["platform"],
            game_type=filters["game_type"],
            status=filters["status"],
            sort_option=filters["sort_option"],
        )

        self._display_games(filtered_games)

    def reset_filters(self):
        self.toolbar.reset_search()
        self.filter_bar.reset()
        self.refresh_library()

    def refresh_library(self):
        games = self.game_repository.get_all_games()

        self.filter_bar.update_options(
            platform_options=(
                self.library_filter_service.get_platform_options(games)
            ),
            status_options=(
                self.library_filter_service.get_status_options(games)
            ),
        )

        self.apply_filters()

    def add_game(self):
        rom_paths = filedialog.askopenfilenames(
            parent=self,
            title="Select Nintendo DS ROM files",
            filetypes=[
                ("Nintendo DS ROMs", "*.nds"),
                ("All Files", "*.*"),
            ],
        )

        if not rom_paths:
            return

        added_count = 0
        skipped_count = 0

        try:
            for rom_path in rom_paths:
                if not rom_path.lower().endswith(".nds"):
                    skipped_count += 1
                    continue

                existing_game = (
                    self.game_repository.get_game_by_rom_path(rom_path)
                )

                if existing_game:
                    skipped_count += 1
                    continue

                self.game_repository.add_local_rom(rom_path)
                added_count += 1

            self.refresh_library()

            messagebox.showinfo(
                "Add Game Complete",
                (
                    f"Added {added_count} game file(s).\n"
                    f"Skipped {skipped_count} file(s)."
                ),
                parent=self,
            )
        except Exception as error:
            messagebox.showerror(
                "Add Game Error",
                str(error),
                parent=self,
            )

    def attach_or_replace_rom(self):
        game = self._get_selected_game()

        if not game:
            return

        selected_path = filedialog.askopenfilename(
            parent=self,
            title=(
                f"{'Replace' if game.rom_path else 'Attach'} "
                f'ROM for "{game.title}"'
            ),
            filetypes=self._get_rom_file_types(game.platform),
        )

        if not selected_path:
            return

        if game.rom_path:
            confirmed = messagebox.askyesno(
                "Replace Attached ROM",
                (
                    f'"{game.title}" already has a ROM attached.\n\n'
                    "Replace it with the selected file?"
                ),
                parent=self,
            )

            if not confirmed:
                return

        try:
            updated_game = self.game_repository.attach_rom_to_game(
                game_id=game.id,
                rom_path=selected_path,
            )

            self._refresh_and_reselect(updated_game.id)

            messagebox.showinfo(
                "ROM Attached",
                (
                    f'ROM attached to "{updated_game.title}".\n\n'
                    f"{updated_game.rom_path}"
                ),
                parent=self,
            )
        except Exception as error:
            messagebox.showerror(
                "Attach ROM Error",
                str(error),
                parent=self,
            )

    def detach_rom(self):
        game = self._get_selected_game()

        if not game:
            return

        if not game.rom_path:
            messagebox.showinfo(
                "No ROM Attached",
                f'"{game.title}" does not have a ROM attached.',
                parent=self,
            )
            return

        confirmed = messagebox.askyesno(
            "Detach ROM",
            (
                f'Detach the ROM from "{game.title}"?\n\n'
                "The ROM file will not be deleted from your computer."
            ),
            parent=self,
        )

        if not confirmed:
            return

        try:
            result = self.game_repository.detach_rom_from_game(
                game.id
            )
            updated_game = result["game"]

            self._refresh_and_reselect(updated_game.id)

            messagebox.showinfo(
                "ROM Detached",
                (
                    f'ROM detached from "{updated_game.title}".\n\n'
                    "The original file was not deleted."
                ),
                parent=self,
            )
        except Exception as error:
            messagebox.showerror(
                "Detach ROM Error",
                str(error),
                parent=self,
            )

    def merge_existing_rom(self):
        target_game = self._get_selected_game()

        if not target_game:
            return

        if target_game.igdb_id is None:
            messagebox.showinfo(
                "IGDB Entry Required",
                (
                    "Select an IGDB metadata entry as the merge target.\n\n"
                    "A personal ROM entry cannot be used as the target."
                ),
                parent=self,
            )
            return

        if target_game.rom_path:
            messagebox.showinfo(
                "ROM Already Attached",
                (
                    f'"{target_game.title}" already has a ROM attached.\n\n'
                    "Detach it before merging another ROM entry."
                ),
                parent=self,
            )
            return

        try:
            candidates = (
                self.game_repository.get_rom_merge_candidates(
                    target_game_id=target_game.id
                )
            )
        except Exception as error:
            messagebox.showerror(
                "Merge ROM Error",
                str(error),
                parent=self,
            )
            return

        if not candidates:
            messagebox.showinfo(
                "No ROM Entries Available",
                (
                    "There are no personal/local ROM entries available "
                    "to merge."
                ),
                parent=self,
            )
            return

        source_game_id = show_rom_merge_dialog(
            parent=self,
            target_game=target_game,
            candidates=candidates,
        )

        if source_game_id is None:
            return

        try:
            result = self.game_repository.merge_local_rom_into_game(
                target_game_id=target_game.id,
                source_game_id=source_game_id,
            )

            merged_game = result["game"]
            removed_source = result["removed_source"]

            self._refresh_and_reselect(merged_game.id)

            messagebox.showinfo(
                "ROM Entry Merged",
                (
                    f'ROM attached to "{merged_game.title}".\n\n'
                    "Removed duplicate local entry:\n"
                    f'{removed_source["title"]}'
                ),
                parent=self,
            )
        except Exception as error:
            messagebox.showerror(
                "Merge ROM Error",
                str(error),
                parent=self,
            )


    def play_selected_game(self):
        """
        Validates the selected game, shows the launch animation, and
        starts the configured emulator when the animation finishes.
        """
        game = self._get_selected_game()

        if not game:
            return

        status = self.emulator_launcher_service.get_launch_status(game)

        if not status["ready"]:
            self._handle_launch_not_ready(
                game=game,
                message=status["message"],
            )
            return

        self.action_bar.set_launching(True)

        self.launch_animation = show_launch_animation(
            parent=self,
            game=game,
            cover_image=self.details_panel.cover_image,
            on_complete=(
                lambda game_id=game.id:
                self._launch_after_animation(game_id)
            ),
        )

    def _launch_after_animation(self, game_id):
        """
        Revalidates and launches the game after the visual animation.
        """
        self.launch_animation = None
        game = self.game_repository.get_game_by_id(game_id)

        try:
            if not game:
                raise EmulatorLaunchError(
                    "The selected game no longer exists."
                )

            self.emulator_launcher_service.launch_game(game)

        except EmulatorLaunchError as error:
            messagebox.showerror(
                "Game Launch Error",
                str(error),
                parent=self,
            )

        finally:
            self.action_bar.set_launching(False)

    def _handle_launch_not_ready(self, game, message):
        """
        Offers the most useful recovery action for a failed validation.
        """
        normalized_message = message.lower()

        if "emulator" in normalized_message:
            configure_now = messagebox.askyesno(
                "Emulator Not Ready",
                (
                    f"{message}\n\n"
                    "Configure an emulator now?"
                ),
                parent=self,
            )

            if configure_now:
                self.open_emulator_configuration()

            return

        if "rom" in normalized_message:
            attach_now = messagebox.askyesno(
                "ROM Not Ready",
                (
                    f"{message}\n\n"
                    "Attach or replace the ROM now?"
                ),
                parent=self,
            )

            if attach_now:
                self.attach_or_replace_rom()

            return

        messagebox.showerror(
            "Game Launch Error",
            message,
            parent=self,
        )

    def delete_selected(self):
        selected_game = self._get_selected_game()

        if not selected_game:
            return

        confirmed = messagebox.askyesno(
            "Delete Game",
            (
                f'Delete "{selected_game.title}" '
                "from the RomDex library?"
            ),
            parent=self,
        )

        if not confirmed:
            return

        try:
            self.game_repository.delete_game(selected_game.id)
            self.refresh_library()
        except Exception as error:
            messagebox.showerror(
                "Delete Error",
                str(error),
                parent=self,
            )

    def open_emulator_configuration(self):
        selected_game = self._get_selected_game(show_warning=False)
        initial_system = "Nintendo DS"

        if (
            selected_game
            and selected_game.platform
            in self.SUPPORTED_EMULATOR_PLATFORMS
        ):
            initial_system = selected_game.platform

        open_emulator_config_dialog(
            parent=self,
            initial_system=initial_system,
            on_saved=self._on_emulator_configuration_changed,
        )

    def _on_emulator_configuration_changed(self, system, emulator):
        selected_game = self._get_selected_game(show_warning=False)

        if selected_game:
            self.details_panel.show_game(selected_game)
            self.action_bar.update_for_game(selected_game)

    def _on_game_selected(self, game_id):
        game = self.game_repository.get_game_by_id(game_id)

        if game:
            self.details_panel.show_game(game)
            self.action_bar.update_for_game(game)
        else:
            self.details_panel.clear()
            self.action_bar.update_for_game(None)

    def _get_selected_game(self, show_warning=True):
        game_id = self.library_table.get_selected_game_id()

        if game_id is None:
            if show_warning:
                messagebox.showwarning(
                    "No Selection",
                    "Please select a game first.",
                    parent=self,
                )
            return None

        game = self.game_repository.get_game_by_id(game_id)

        if not game and show_warning:
            messagebox.showerror(
                "Game Not Found",
                "The selected game no longer exists.",
                parent=self,
            )

        return game

    def _display_games(self, games):
        self.library_table.display_games(
            games,
            game_type_resolver=(
                self.library_filter_service.get_game_type
            ),
        )
        self.details_panel.clear()
        self.action_bar.update_for_game(None)

    def _refresh_and_reselect(self, game_id):
        self.refresh_library()

        if self.library_table.select_game(game_id):
            return

        self.details_panel.clear()
        self.action_bar.update_for_game(None)

    def _get_rom_file_types(self, platform):
        return self.ROM_FILE_TYPES.get(
            platform,
            [
                (
                    "Supported ROMs",
                    "*.nds *.3ds *.cci *.cxi",
                ),
                ("All Files", "*.*"),
            ],
        )

    def _open_discovery(self):
        if self.on_discover_requested:
            self.on_discover_requested()

    def _quit(self):
        if self.on_quit_requested:
            self.on_quit_requested()

    def close(self):
        if self.launch_animation is not None:
            try:
                self.launch_animation.cancel()
            except Exception:
                pass

        self.game_repository.close()
