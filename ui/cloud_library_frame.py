import threading
import tkinter as tk
from tkinter import messagebox, ttk

from repositories.game_repository import GameRepository
from services.cloud.cloud_config_service import (
    CloudConfigError,
    CloudConfigService
)
from services.cloud.cloud_library_service import CloudLibraryService
from services.cloud.library_share_service import LibraryShareService


class CloudLibraryFrame(ttk.Frame):
    """RomDex cloud snapshot and read-only metadata sharing UI."""

    def __init__(self, parent, on_library_changed=None):
        super().__init__(parent)

        self.on_library_changed = on_library_changed
        self.config_service = CloudConfigService()
        self.cloud_library_service = CloudLibraryService(
            config_service=self.config_service
        )
        self.library_share_service = LibraryShareService(
            cloud_library_service=self.cloud_library_service
        )
        self._busy = False
        self.import_mode_var = tk.StringVar(
            master=self,
            value=GameRepository.IMPORT_MODE_MERGE
        )

        self._create_widgets()
        self.refresh_status()

    def _create_widgets(self):
        ttk.Label(
            self,
            text="Cloud Library",
            font=("Arial", 20, "bold")
        ).pack(pady=(20, 5))

        ttk.Label(
            self,
            text=(
                "Back up your metadata and import read-only libraries "
                "using a Share Key."
            )
        ).pack(pady=(0, 15))

        self._create_connection_frame()
        self._create_sync_frame()
        self._create_import_frame()
        self._create_activity_frame()

    def _create_connection_frame(self):
        frame = ttk.LabelFrame(self, text="Connection", padding=15)
        frame.pack(fill="x", padx=25, pady=(0, 15))

        labels = (
            ("Status:", 0),
            ("Library name:", 1),
            ("Library ID:", 2),
            ("Share key:", 3)
        )
        for text, row in labels:
            ttk.Label(frame, text=text).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 10),
                pady=4
            )

        self.connection_status_value = ttk.Label(frame, text="Checking...")
        self.connection_status_value.grid(row=0, column=1, sticky="w", pady=4)

        self.library_name_value = ttk.Label(frame, text="Not connected")
        self.library_name_value.grid(row=1, column=1, sticky="w", pady=4)

        self.library_id_value = ttk.Label(frame, text="Not created")
        self.library_id_value.grid(row=2, column=1, sticky="w", pady=4)

        self.share_key_value = ttk.Entry(frame, state="readonly", width=55)
        self.share_key_value.grid(row=3, column=1, sticky="ew", pady=4)
        frame.columnconfigure(1, weight=1)

    def _create_sync_frame(self):
        frame = ttk.LabelFrame(self, text="My Cloud Library", padding=15)
        frame.pack(fill="x", padx=25, pady=(0, 15))

        ttk.Label(
            frame,
            text=(
                "Sync saves this PC's current game metadata as your cloud "
                "library. Cloud-only metadata is removed so it matches this "
                "PC. ROM files and local paths never leave the computer."
            ),
            wraplength=900
        ).pack(anchor="w", pady=(0, 10))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")

        self.sync_button = ttk.Button(
            buttons,
            text="Sync Local Library",
            command=self._sync_library
        )
        self.sync_button.pack(side="left", padx=(0, 8))

        self.copy_share_button = ttk.Button(
            buttons,
            text="Copy Share Key",
            command=self._copy_share_key
        )
        self.copy_share_button.pack(side="left", padx=8)

        self.refresh_button = ttk.Button(
            buttons,
            text="Refresh Status",
            command=self.refresh_status
        )
        self.refresh_button.pack(side="left", padx=8)

    def _create_import_frame(self):
        frame = ttk.LabelFrame(self, text="Import Shared Library", padding=15)
        frame.pack(fill="x", padx=25, pady=(0, 15))

        ttk.Label(frame, text="Share key:").pack(anchor="w")

        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill="x", pady=(6, 2))

        merge_button = ttk.Radiobutton(
            mode_frame,
            text="Add — keep my library and add games I do not have",
            variable=self.import_mode_var,
            value=GameRepository.IMPORT_MODE_MERGE
        )
        merge_button.pack(side="left", padx=(0, 18))

        overwrite_button = ttk.Radiobutton(
            mode_frame,
            text="Overwrite — use the shared metadata library",
            variable=self.import_mode_var,
            value=GameRepository.IMPORT_MODE_OVERWRITE
        )
        overwrite_button.pack(side="left")
        self.import_mode_buttons = (merge_button, overwrite_button)

        entry_frame = ttk.Frame(frame)
        entry_frame.pack(fill="x", pady=(6, 8))

        self.import_share_entry = ttk.Entry(entry_frame)
        self.import_share_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )
        self.import_share_entry.bind(
            "<Return>",
            lambda event: self._import_shared_library()
        )

        self.import_button = ttk.Button(
            entry_frame,
            text="Import Library",
            command=self._import_shared_library
        )
        self.import_button.pack(side="right")

        ttk.Label(
            frame,
            text=(
                "Overwrite replaces this PC's RomDex metadata with the "
                "shared library. Your own cloud library and Share Key stay "
                "yours. ROM files are never deleted."
            ),
            wraplength=900
        ).pack(anchor="w")

    def _create_activity_frame(self):
        frame = ttk.LabelFrame(self, text="Activity", padding=15)
        frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        self.activity_text = tk.Text(
            frame,
            height=9,
            wrap="word",
            state="disabled"
        )
        self.activity_text.pack(fill="both", expand=True)
        self._set_activity("Cloud controls are ready.")

    def refresh_status(self):
        try:
            config = self.config_service.load_config()
        except CloudConfigError as error:
            self.connection_status_value.config(text="Configuration error")
            self._set_activity(str(error))
            return

        if not config:
            self.connection_status_value.config(text="Not connected")
            self.library_name_value.config(text="No cloud library yet")
            self.library_id_value.config(text="Not created")
            self._set_readonly_entry(self.share_key_value, "")
            self.copy_share_button.config(state="disabled")
            return

        self.connection_status_value.config(text="Connected")
        self.library_name_value.config(
            text=config.get("library_name", "My RomDex Library")
        )
        self.library_id_value.config(text=config.get("library_id", "Unknown"))
        self._set_readonly_entry(
            self.share_key_value,
            config.get("share_id", "")
        )
        self.copy_share_button.config(state="normal")

    def _sync_library(self):
        if self._busy:
            return

        self._set_busy(True)
        self._set_activity("Saving this PC's metadata snapshot to Firestore...")
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def _sync_worker(self):
        repository = GameRepository()
        try:
            result = self.cloud_library_service.sync_library(
                games=repository.get_all_games(),
                library_name="My RomDex Library"
            )
            self.after(0, lambda: self._finish_sync(result))
        except Exception as error:
            self.after(
                0,
                lambda error=error: self._show_operation_error(
                    "Cloud Sync Failed",
                    error
                )
            )
        finally:
            repository.close()

    def _finish_sync(self, result):
        self._set_busy(False)
        self.refresh_status()
        action = "Created" if result.get("created_new_library") else "Updated"
        self._set_activity(
            f"{action} cloud library {result['library_id']}.\n"
            f"Uploaded or updated: {result['uploaded_count']}\n"
            f"Removed from cloud: {result['deleted_count']}\n"
            f"Duplicate local identities skipped: {result['duplicate_count']}\n"
            f"Final cloud total: {result['cloud_game_count']}"
        )
        messagebox.showinfo(
            "Cloud Sync Complete",
            f"Saved {result['cloud_game_count']} game record(s) to the cloud.\n"
            f"Removed {result['deleted_count']} old cloud record(s).",
            parent=self
        )

    def _copy_share_key(self):
        try:
            share_key = self.config_service.get_share_id()
        except CloudConfigError as error:
            messagebox.showerror("Copy Failed", str(error), parent=self)
            return

        if not share_key:
            messagebox.showwarning(
                "No Share Key",
                "Sync the library first to create a Share Key.",
                parent=self
            )
            return

        self.clipboard_clear()
        self.clipboard_append(share_key)
        self.update()
        self._set_activity("Share Key copied to the clipboard.")

    def _import_shared_library(self):
        if self._busy:
            return

        share_key = self.import_share_entry.get().strip()
        if not share_key:
            messagebox.showwarning(
                "Missing Share Key",
                "Enter a RomDex Share Key.",
                parent=self
            )
            return

        mode = self.import_mode_var.get()
        if (
            mode == GameRepository.IMPORT_MODE_OVERWRITE
            and not self._confirm_overwrite()
        ):
            return

        self._set_busy(True)
        self._set_activity(f"Importing shared metadata using {mode} mode...")
        threading.Thread(
            target=self._import_worker,
            args=(share_key, mode),
            daemon=True
        ).start()

    def _import_worker(self, share_key, mode):
        repository = GameRepository()
        try:
            result = self.library_share_service.import_shared_library(
                share_key=share_key,
                game_repository=repository,
                mode=mode
            )
            self.after(0, lambda: self._finish_import(result))
        except Exception as error:
            self.after(
                0,
                lambda error=error: self._show_operation_error(
                    "Import Failed",
                    error
                )
            )
        finally:
            repository.close()

    def _finish_import(self, result):
        self._set_busy(False)
        name = result["library"].get("name", "Shared Library")
        removed_count = result.get("removed_count", 0)
        preserved_files = result.get("preserved_rom_file_count", 0)
        self._set_activity(
            f'Imported "{name}".\n'
            f"New games: {result['imported_count']}\n"
            f"Matching games updated: {result['updated_count']}\n"
            f"Duplicates skipped: {result['skipped_count']}\n"
            f"Old local records removed: {removed_count}\n"
            f"ROM files left safely on disk: {preserved_files}"
        )
        self.import_share_entry.delete(0, tk.END)

        if self.on_library_changed:
            self.on_library_changed()

        messagebox.showinfo(
            "Shared Library Imported",
            f"Added {result['imported_count']} game(s).\n"
            f"Updated {result['updated_count']} matching game(s).\n"
            f"Removed {removed_count} old local record(s).\n"
            "Your Share Key did not change and no ROM files were deleted.",
            parent=self
        )

    def _confirm_overwrite(self):
        return messagebox.askyesno(
            "Overwrite Current Library?",
            "Overwrite makes this PC's RomDex metadata match the shared "
            "library. Local records absent from the shared library will be "
            "removed.\n\nYour own cloud library and Share Key remain yours. "
            "ROM files stay on the computer, but unmatched files will need "
            "to be added to RomDex again.\n\nContinue?",
            parent=self
        )

    def _show_operation_error(self, title, error):
        self._set_busy(False)
        self._set_activity(str(error))
        messagebox.showerror(title, str(error), parent=self)

    def _set_busy(self, busy):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.sync_button.config(state=state)
        self.import_button.config(state=state)
        self.refresh_button.config(state=state)

        for button in self.import_mode_buttons:
            button.config(state=state)

        if busy:
            self.copy_share_button.config(state="disabled")
        else:
            self.refresh_status()

    def _set_activity(self, message):
        self.activity_text.config(state="normal")
        self.activity_text.delete("1.0", tk.END)
        self.activity_text.insert(tk.END, message)
        self.activity_text.config(state="disabled")

    @staticmethod
    def _set_readonly_entry(entry, value):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.config(state="readonly")
