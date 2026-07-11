import threading
import tkinter as tk
from tkinter import messagebox, ttk

from services.cloud.cloud_config_service import (
    CloudConfigError,
    CloudConfigService
)
from services.cloud.cloud_library_service import (
    CloudLibraryError,
    CloudLibraryService
)
from repositories.game_repository import GameRepository

from services.cloud.library_share_service import (
    LibraryShareError,
    LibraryShareService
)


class CloudLibraryFrame(ttk.Frame):
    """
    Tkinter interface for RomDex cloud synchronization and sharing.

    The frame delegates Firebase and Firestore operations to the cloud
    service classes and keeps network work off the Tkinter UI thread.
    """

    def __init__(
        self,
        parent,
        on_library_changed=None
    ):
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
        self._create_widgets()
        self.refresh_status()

    def _create_widgets(self):
        title_label = ttk.Label(
            self,
            text="Cloud Library",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=(20, 5))

        subtitle_label = ttk.Label(
            self,
            text=(
                "Synchronize library metadata and import "
                "read-only shared libraries."
            )
        )
        subtitle_label.pack(pady=(0, 15))

        status_frame = ttk.LabelFrame(
            self,
            text="Connection",
            padding=15
        )
        status_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        ttk.Label(
            status_frame,
            text="Status:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=4
        )

        self.connection_status_value = ttk.Label(
            status_frame,
            text="Checking..."
        )
        self.connection_status_value.grid(
            row=0,
            column=1,
            sticky="w",
            pady=4
        )

        ttk.Label(
            status_frame,
            text="Library name:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=4
        )

        self.library_name_value = ttk.Label(
            status_frame,
            text="Not connected"
        )
        self.library_name_value.grid(
            row=1,
            column=1,
            sticky="w",
            pady=4
        )

        ttk.Label(
            status_frame,
            text="Library ID:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=4
        )

        self.library_id_value = ttk.Label(
            status_frame,
            text="Not created"
        )
        self.library_id_value.grid(
            row=2,
            column=1,
            sticky="w",
            pady=4
        )

        ttk.Label(
            status_frame,
            text="Share key:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=4
        )

        self.share_key_value = ttk.Entry(
            status_frame,
            state="readonly",
            width=55
        )
        self.share_key_value.grid(
            row=3,
            column=1,
            sticky="ew",
            pady=4
        )

        status_frame.columnconfigure(
            1,
            weight=1
        )

        action_frame = ttk.LabelFrame(
            self,
            text="My Cloud Library",
            padding=15
        )
        action_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        self.sync_button = ttk.Button(
            action_frame,
            text="Sync Local Library",
            command=self._sync_library
        )
        self.sync_button.pack(
            side="left",
            padx=(0, 8)
        )

        self.copy_share_button = ttk.Button(
            action_frame,
            text="Copy Share Key",
            command=self._copy_share_key
        )
        self.copy_share_button.pack(
            side="left",
            padx=8
        )

        self.refresh_button = ttk.Button(
            action_frame,
            text="Refresh Status",
            command=self.refresh_status
        )
        self.refresh_button.pack(
            side="left",
            padx=8
        )

        import_frame = ttk.LabelFrame(
            self,
            text="Import Shared Library",
            padding=15
        )
        import_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        ttk.Label(
            import_frame,
            text="Public share key:"
        ).pack(
            anchor="w"
        )

        import_entry_frame = ttk.Frame(
            import_frame
        )
        import_entry_frame.pack(
            fill="x",
            pady=(6, 8)
        )

        self.import_share_entry = ttk.Entry(
            import_entry_frame
        )
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
            import_entry_frame,
            text="Import Library",
            command=self._import_shared_library
        )
        self.import_button.pack(
            side="right"
        )

        ttk.Label(
            import_frame,
            text=(
                "Only game metadata is imported. "
                "ROM files and device-specific paths are never downloaded."
            ),
            wraplength=850
        ).pack(
            anchor="w"
        )

        activity_frame = ttk.LabelFrame(
            self,
            text="Activity",
            padding=15
        )
        activity_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20)
        )

        self.activity_text = tk.Text(
            activity_frame,
            height=10,
            wrap="word",
            state="disabled"
        )
        self.activity_text.pack(
            fill="both",
            expand=True
        )

        self._set_activity(
            "Cloud controls are ready."
        )

    def refresh_status(self):
        """
        Loads locally remembered cloud-library information.
        """
        try:
            config = self.config_service.load_config()
        except CloudConfigError as error:
            self.connection_status_value.config(
                text="Configuration error"
            )
            self._set_activity(str(error))
            return

        if not config:
            self.connection_status_value.config(
                text="Not connected"
            )
            self.library_name_value.config(
                text="No cloud library yet"
            )
            self.library_id_value.config(
                text="Not created"
            )
            self._set_readonly_entry(
                self.share_key_value,
                ""
            )
            self.copy_share_button.config(
                state="disabled"
            )
            return

        self.connection_status_value.config(
            text="Connected"
        )
        self.library_name_value.config(
            text=config.get(
                "library_name",
                "My RomDex Library"
            )
        )
        self.library_id_value.config(
            text=config.get(
                "library_id",
                "Unknown"
            )
        )
        self._set_readonly_entry(
            self.share_key_value,
            config.get("share_id", "")
        )
        self.copy_share_button.config(
            state="normal"
        )

    def _sync_library(self):
        if self._busy:
            return

        self._set_busy(True)
        self._set_activity(
            "Synchronizing local library with Firestore..."
        )

        thread = threading.Thread(
            target=self._sync_worker,
            daemon=True
        )
        thread.start()

    def _sync_worker(self):
        repository = GameRepository()

        try:
            games = repository.get_all_games()

            result = (
                self.cloud_library_service.sync_library(
                    games=games,
                    library_name="My RomDex Library"
                )
            )

            self.after(
                0,
                lambda: self._finish_sync(result)
            )

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

        if result.get("created_new_library"):
            action_text = "Created and synchronized"
        else:
            action_text = "Updated"

        self._set_activity(
            f"{action_text} cloud library "
            f"{result['library_id']}.\n"
            f"Uploaded {result['uploaded_count']} game record(s)."
        )

        messagebox.showinfo(
            "Cloud Sync Complete",
            f"Uploaded {result['uploaded_count']} game record(s)."
        )

    def _copy_share_key(self):
        try:
            share_key = (
                self.config_service.get_share_id()
            )
        except CloudConfigError as error:
            messagebox.showerror(
                "Copy Failed",
                str(error)
            )
            return

        if not share_key:
            messagebox.showwarning(
                "No Share Key",
                "Sync the library first to create a share key."
            )
            return

        self.clipboard_clear()
        self.clipboard_append(share_key)
        self.update()

        self._set_activity(
            "Public share key copied to the clipboard."
        )

    def _import_shared_library(self):
        if self._busy:
            return

        share_key = (
            self.import_share_entry
            .get()
            .strip()
        )

        if not share_key:
            messagebox.showwarning(
                "Missing Share Key",
                "Enter a RomDex public share key."
            )
            return

        self._set_busy(True)
        self._set_activity(
            "Downloading and importing shared library metadata..."
        )

        thread = threading.Thread(
            target=self._import_worker,
            args=(share_key,),
            daemon=True
        )
        thread.start()

    def _import_worker(self, share_key):
        repository = GameRepository()

        try:
            result = (
                self.library_share_service
                .import_shared_library(
                    share_key=share_key,
                    game_repository=repository
                )
            )

            self.after(
                0,
                lambda: self._finish_import(result)
            )

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

        library_name = (
            result["library"]
            .get("name", "Shared Library")
        )

        self._set_activity(
            f'Imported "{library_name}".\n'
            f"New games: {result['imported_count']}\n"
            f"Duplicates skipped: {result['skipped_count']}"
        )

        self.import_share_entry.delete(
            0,
            tk.END
        )

        if self.on_library_changed:
            self.on_library_changed()

        messagebox.showinfo(
            "Shared Library Imported",
            f"Imported {result['imported_count']} new game(s).\n"
            f"Skipped {result['skipped_count']} duplicate(s)."
        )

    def _show_operation_error(self, title, error):
        self._set_busy(False)
        self._set_activity(str(error))

        messagebox.showerror(
            title,
            str(error)
        )

    def _set_busy(self, busy):
        self._busy = busy
        state = "disabled" if busy else "normal"

        self.sync_button.config(
            state=state
        )
        self.import_button.config(
            state=state
        )
        self.refresh_button.config(
            state=state
        )

        if busy:
            self.copy_share_button.config(
                state="disabled"
            )
        else:
            self.refresh_status()

    def _set_activity(self, message):
        self.activity_text.config(
            state="normal"
        )
        self.activity_text.delete(
            "1.0",
            tk.END
        )
        self.activity_text.insert(
            tk.END,
            message
        )
        self.activity_text.config(
            state="disabled"
        )

    @staticmethod
    def _set_readonly_entry(entry, value):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.config(state="readonly")
