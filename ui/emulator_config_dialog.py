import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from services.emulator.emulator_config_service import (
    EmulatorConfigError,
    EmulatorConfigService
)


class EmulatorConfigDialog(tk.Toplevel):
    """
    Modal dialog for configuring emulators used by RomDex.
    """

    SYSTEMS = (
        "Nintendo DS",
        "Nintendo DSi",
        "Nintendo 3DS"
    )

    def __init__(
        self,
        parent,
        initial_system="Nintendo DS",
        config_service=None,
        on_saved=None
    ):
        super().__init__(parent)

        self.config_service = (
            config_service
            if config_service is not None
            else EmulatorConfigService()
        )
        self.on_saved = on_saved

        self.title("Configure Emulator")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.system_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Choose a system to view its emulator settings."
        )

        self._create_widgets()
        self._select_initial_system(initial_system)
        self._load_selected_system()

        self.update_idletasks()
        self._centre_over_parent(parent)

        self.grab_set()
        self.focus_force()

    def _create_widgets(self):
        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Emulator Configuration",
            font=("Arial", 15, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 14)
        )

        ttk.Label(
            container,
            text="System:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=5
        )

        self.system_combobox = ttk.Combobox(
            container,
            textvariable=self.system_var,
            values=self.SYSTEMS,
            state="readonly",
            width=28
        )
        self.system_combobox.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=5
        )
        self.system_combobox.bind(
            "<<ComboboxSelected>>",
            self._on_system_changed
        )

        ttk.Label(
            container,
            text="Emulator name:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=5
        )

        self.name_entry = ttk.Entry(
            container,
            textvariable=self.name_var,
            width=38
        )
        self.name_entry.grid(
            row=2,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=5
        )

        ttk.Label(
            container,
            text="Executable:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=5
        )

        self.path_entry = ttk.Entry(
            container,
            textvariable=self.path_var,
            width=48
        )
        self.path_entry.grid(
            row=3,
            column=1,
            sticky="ew",
            pady=5
        )

        ttk.Button(
            container,
            text="Browse...",
            command=self._browse_for_executable
        ).grid(
            row=3,
            column=2,
            padx=(8, 0),
            pady=5
        )

        status_frame = ttk.LabelFrame(
            container,
            text="Status",
            padding=10
        )
        status_frame.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(14, 10)
        )

        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            wraplength=470,
            justify="left"
        )
        self.status_label.pack(
            fill="x",
            expand=True
        )

        button_frame = ttk.Frame(container)
        button_frame.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(6, 0)
        )

        ttk.Button(
            button_frame,
            text="Save",
            command=self._save
        ).pack(
            side="left"
        )

        ttk.Button(
            button_frame,
            text="Remove",
            command=self._remove
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            button_frame,
            text="Close",
            command=self._close
        ).pack(
            side="right"
        )

        container.columnconfigure(
            1,
            weight=1
        )

    def _select_initial_system(self, initial_system):
        if initial_system in self.SYSTEMS:
            self.system_var.set(initial_system)
        else:
            self.system_var.set("Nintendo DS")

    def _on_system_changed(self, event=None):
        self._load_selected_system()

    def _load_selected_system(self):
        system = self.system_var.get()

        try:
            emulator = self.config_service.get_emulator(system)
        except EmulatorConfigError as error:
            self.name_var.set("")
            self.path_var.set("")
            self.status_var.set(str(error))
            return

        if not emulator:
            self.name_var.set("")
            self.path_var.set("")
            self.status_var.set(
                f'No emulator is configured for "{system}".'
            )
            return

        emulator_name = emulator.get("name", "")
        executable_path = emulator.get(
            "executable_path",
            ""
        )

        self.name_var.set(emulator_name)
        self.path_var.set(executable_path)

        if self.config_service.is_configured(system):
            self.status_var.set(
                f'Ready: {emulator_name} is configured for "{system}".'
            )
        else:
            self.status_var.set(
                "The saved emulator executable could not be found. "
                "Browse for it again and save the new path."
            )

    def _browse_for_executable(self):
        selected_path = filedialog.askopenfilename(
            parent=self,
            title="Select Emulator Executable",
            filetypes=[
                ("Windows applications", "*.exe"),
                ("All files", "*.*")
            ]
        )

        if not selected_path:
            return

        self.path_var.set(selected_path)

        if not self.name_var.get().strip():
            self.name_var.set(
                Path(selected_path).stem
            )

        self.status_var.set(
            "Executable selected. Click Save to store it."
        )

    def _save(self):
        system = self.system_var.get()
        emulator_name = self.name_var.get().strip()
        executable_path = self.path_var.get().strip()

        try:
            saved = self.config_service.save_emulator(
                system=system,
                emulator_name=emulator_name,
                executable_path=executable_path
            )

        except EmulatorConfigError as error:
            messagebox.showerror(
                "Emulator Configuration Error",
                str(error),
                parent=self
            )
            self.status_var.set(str(error))
            return

        self.name_var.set(saved["name"])
        self.path_var.set(
            saved["executable_path"]
        )
        self.status_var.set(
            f'Ready: {saved["name"]} is configured for "{system}".'
        )

        if self.on_saved:
            self.on_saved(
                system,
                saved.copy()
            )

        messagebox.showinfo(
            "Emulator Saved",
            f'{saved["name"]} is now configured for {system}.',
            parent=self
        )

    def _remove(self):
        system = self.system_var.get()

        try:
            emulator = self.config_service.get_emulator(system)
        except EmulatorConfigError as error:
            messagebox.showerror(
                "Emulator Configuration Error",
                str(error),
                parent=self
            )
            return

        if not emulator:
            messagebox.showinfo(
                "Nothing to Remove",
                f'No emulator is configured for "{system}".',
                parent=self
            )
            return

        confirmed = messagebox.askyesno(
            "Remove Emulator",
            (
                f'Remove {emulator.get("name", "the emulator")} '
                f'from "{system}" configuration?'
            ),
            parent=self
        )

        if not confirmed:
            return

        try:
            removed = self.config_service.remove_emulator(
                system
            )
        except EmulatorConfigError as error:
            messagebox.showerror(
                "Emulator Configuration Error",
                str(error),
                parent=self
            )
            return

        self.name_var.set("")
        self.path_var.set("")
        self.status_var.set(
            f'No emulator is configured for "{system}".'
        )

        if self.on_saved:
            self.on_saved(
                system,
                None
            )

        if removed:
            messagebox.showinfo(
                "Emulator Removed",
                f'Emulator configuration removed for "{system}".',
                parent=self
            )

    def _centre_over_parent(self, parent):
        parent.update_idletasks()

        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + max(
            0,
            (parent_width - width) // 2
        )
        y = parent_y + max(
            0,
            (parent_height - height) // 2
        )

        self.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def _close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass

        self.destroy()


def open_emulator_config_dialog(
    parent,
    initial_system="Nintendo DS",
    config_service=None,
    on_saved=None
):
    """
    Convenience function used by LibraryFrame or App.
    """
    return EmulatorConfigDialog(
        parent=parent,
        initial_system=initial_system,
        config_service=config_service,
        on_saved=on_saved
    )
