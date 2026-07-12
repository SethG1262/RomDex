import time
import tkinter as tk
from tkinter import ttk


class LaunchAnimationDialog(tk.Toplevel):
    """
    Brief non-blocking animation displayed before an emulator launches.

    The animation uses Tkinter's after() scheduler rather than
    time.sleep(), so the rest of the interface remains responsive.
    """

    # Reduced from 1300 ms for a faster perceived launch.
    DURATION_MS = 800

    # Approximately 60 FPS.
    FRAME_INTERVAL_MS = 16

    def __init__(
        self,
        parent,
        game,
        cover_image=None,
        on_complete=None,
    ):
        super().__init__(parent)

        self.parent = parent
        self.game = game
        self.cover_image = cover_image
        self.on_complete = on_complete

        self.started_at = None
        self.after_id = None
        self.is_finished = False
        self.supports_alpha = False

        self.title("Launching Game")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.status_var = tk.StringVar(
            value="Preparing launch..."
        )
        self.progress_var = tk.DoubleVar(value=0.0)

        self._create_widgets()
        self.update_idletasks()
        self._centre_over_parent()

        self._prepare_fade()
        self.grab_set()
        self.focus_force()

        self.started_at = time.monotonic()
        self.after_id = self.after(
            self.FRAME_INTERVAL_MS,
            self._animate,
        )

    def _create_widgets(self):
        container = ttk.Frame(self, padding=22)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="RomDex",
            font=("Arial", 17, "bold"),
        ).pack(pady=(0, 12))

        cover_frame = ttk.Frame(
            container,
            width=260,
            height=360,
        )
        cover_frame.pack()
        cover_frame.pack_propagate(False)

        if self.cover_image is not None:
            cover_label = ttk.Label(
                cover_frame,
                image=self.cover_image,
                anchor="center",
            )
        else:
            cover_label = ttk.Label(
                cover_frame,
                text="ROMDEX",
                anchor="center",
                font=("Arial", 28, "bold"),
            )

        cover_label.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text=self.game.title,
            font=("Arial", 14, "bold"),
            anchor="center",
            justify="center",
            wraplength=360,
        ).pack(fill="x", pady=(16, 4))

        ttk.Label(
            container,
            text=self.game.platform or "Unknown Platform",
            anchor="center",
        ).pack(fill="x")

        ttk.Label(
            container,
            textvariable=self.status_var,
            anchor="center",
        ).pack(fill="x", pady=(18, 7))

        ttk.Progressbar(
            container,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            length=340,
        ).pack(fill="x")

    def _animate(self):
        if self.is_finished or self.started_at is None:
            return

        elapsed_ms = (
            time.monotonic() - self.started_at
        ) * 1000

        progress = min(
            100.0,
            elapsed_ms / self.DURATION_MS * 100.0,
        )

        self.progress_var.set(progress)
        self._update_status(progress)
        self._update_fade(progress)

        if progress >= 100.0:
            self.progress_var.set(100.0)
            self.status_var.set("Launching...")

            # Launch immediately when the bar completes.
            # The old implementation waited another 100 ms here.
            self._finish()
            return

        self.after_id = self.after(
            self.FRAME_INTERVAL_MS,
            self._animate,
        )

    def _update_status(self, progress):
        dot_count = (
            int(progress // 10) % 3
        ) + 1
        dots = "." * dot_count

        if progress < 30:
            status = "Checking ROM"
        elif progress < 65:
            status = "Preparing emulator"
        elif progress < 90:
            status = "Loading game"
        else:
            status = "Launching"

        self.status_var.set(f"{status}{dots}")

    def _prepare_fade(self):
        try:
            self.attributes("-alpha", 0.0)
            self.supports_alpha = True
        except tk.TclError:
            self.supports_alpha = False

    def _update_fade(self, progress):
        """
        Uses only a quick fade-in.

        Removing the fade-out prevents the animation from visually
        lingering after the progress bar is complete.
        """
        if not self.supports_alpha:
            return

        try:
            if progress < 12:
                alpha = max(
                    0.10,
                    progress / 12,
                )
            else:
                alpha = 1.0

            self.attributes("-alpha", alpha)
        except tk.TclError:
            self.supports_alpha = False

    def _finish(self):
        if self.is_finished:
            return

        self.is_finished = True
        callback = self.on_complete
        self._close()

        # Call directly instead of waiting for another idle event.
        if callback and self.parent.winfo_exists():
            callback()

    def cancel(self):
        """
        Closes the animation without launching the game.
        """
        if self.is_finished:
            return

        self.is_finished = True
        self.on_complete = None
        self._close()

    def _close(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except tk.TclError:
                pass

            self.after_id = None

        try:
            self.grab_release()
        except tk.TclError:
            pass

        try:
            self.destroy()
        except tk.TclError:
            pass

    def _centre_over_parent(self):
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        self.parent.update_idletasks()

        x = self.parent.winfo_rootx() + max(
            0,
            (self.parent.winfo_width() - width) // 2,
        )
        y = self.parent.winfo_rooty() + max(
            0,
            (self.parent.winfo_height() - height) // 2,
        )

        self.geometry(f"{width}x{height}+{x}+{y}")


def show_launch_animation(
    parent,
    game,
    cover_image=None,
    on_complete=None,
):
    """
    Opens the animation and returns its dialog instance.
    """
    return LaunchAnimationDialog(
        parent=parent,
        game=game,
        cover_image=cover_image,
        on_complete=on_complete,
    )
