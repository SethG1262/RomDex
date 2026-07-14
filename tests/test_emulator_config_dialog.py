import tkinter as tk
from tkinter import ttk

from ui.emulator_config_dialog import (
    open_emulator_config_dialog
)


class EmulatorDialogTestApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RomDex Emulator Dialog Test")
        self.geometry("520x240")

        container = ttk.Frame(
            self,
            padding=24
        )
        container.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            container,
            text="Emulator Configuration Dialog Test",
            font=("Arial", 15, "bold")
        ).pack(
            pady=(0, 14)
        )

        self.result_var = tk.StringVar(
            value="No configuration changes reported yet."
        )

        ttk.Label(
            container,
            textvariable=self.result_var,
            wraplength=440,
            justify="center"
        ).pack(
            pady=10
        )

        ttk.Button(
            container,
            text="Configure Emulator",
            command=self._open_dialog
        ).pack(
            pady=12
        )

    def _open_dialog(self):
        open_emulator_config_dialog(
            parent=self,
            initial_system="Nintendo DS",
            on_saved=self._on_configuration_changed
        )

    def _on_configuration_changed(
        self,
        system,
        emulator
    ):
        if emulator:
            self.result_var.set(
                f'{emulator["name"]} saved for {system}.'
            )
        else:
            self.result_var.set(
                f"Configuration removed for {system}."
            )


if __name__ == "__main__":
    app = EmulatorDialogTestApp()
    app.mainloop()