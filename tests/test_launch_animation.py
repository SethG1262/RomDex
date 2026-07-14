import tkinter as tk
from tkinter import ttk

from ui.launch_animation_dialog import show_launch_animation


class MockGame:
    title = "RomDex Animation Test"
    platform = "Nintendo DS"


class LaunchAnimationTestApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Launch Animation Test")
        self.geometry("520x230")

        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="RomDex Launch Animation",
            font=("Arial", 16, "bold"),
        ).pack(pady=(0, 18))

        self.status_var = tk.StringVar(
            value="Press the button to preview the animation."
        )

        ttk.Label(
            container,
            textvariable=self.status_var,
            wraplength=440,
            justify="center",
        ).pack(pady=8)

        ttk.Button(
            container,
            text="Preview Animation",
            command=self._preview,
        ).pack(pady=14)

    def _preview(self):
        self.status_var.set("Animation running...")

        show_launch_animation(
            parent=self,
            game=MockGame(),
            on_complete=self._completed,
        )

    def _completed(self):
        self.status_var.set(
            "Animation completed. The real Library button "
            "would launch the emulator now."
        )


if __name__ == "__main__":
    app = LaunchAnimationTestApp()
    app.mainloop()
