import tkinter as tk
from tkinter import messagebox, ttk


class RomMergeDialog(tk.Toplevel):
    """
    Modal picker for choosing a local ROM entry to merge into an IGDB
    metadata entry.
    """

    def __init__(self, parent, target_game, candidates):
        super().__init__(parent)

        self.target_game = target_game
        self.result_source_id = None

        self.title("Merge Existing ROM")
        self.geometry("760x430")
        self.minsize(650, 360)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._create_widgets(candidates)
        self._centre_over_parent(parent)

        self.grab_set()
        self.focus_force()

    def _create_widgets(self, candidates):
        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Merge Existing ROM",
            font=("Arial", 15, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=(
                f'Target: "{self.target_game.title}"\n'
                "Choose the personal ROM entry whose file should be "
                "attached to this IGDB entry."
            ),
            justify="left",
            wraplength=700,
        ).pack(anchor="w", pady=(6, 14))

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)

        columns = ("title", "platform", "rom_path")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.table.heading("title", text="Local Entry")
        self.table.heading("platform", text="Platform")
        self.table.heading("rom_path", text="ROM Path")

        self.table.column("title", width=190)
        self.table.column("platform", width=120)
        self.table.column("rom_path", width=390)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview,
        )
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(side="right", fill="y")

        for game in candidates:
            self.table.insert(
                "",
                "end",
                iid=str(game.id),
                values=(
                    game.title,
                    game.platform or "Unknown",
                    game.rom_path or "No ROM path",
                ),
            )

        self.table.bind(
            "<Double-1>",
            lambda event: self._confirm_merge(),
        )

        ttk.Label(
            container,
            text=(
                "The selected local-only row will be removed after its "
                "ROM is transferred. The ROM file itself will not be "
                "deleted."
            ),
            wraplength=700,
            justify="left",
        ).pack(anchor="w", pady=(12, 8))

        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x")

        ttk.Button(
            button_frame,
            text="Merge Selected",
            command=self._confirm_merge,
        ).pack(side="left")

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
        ).pack(side="right")

    def _confirm_merge(self):
        selection = self.table.selection()

        if not selection:
            messagebox.showwarning(
                "No ROM Selected",
                "Select a personal ROM entry first.",
                parent=self,
            )
            return

        source_id = int(selection[0])
        values = self.table.item(selection[0], "values")
        source_title = values[0] if values else "selected entry"

        confirmed = messagebox.askyesno(
            "Confirm ROM Merge",
            (
                f'Merge "{source_title}" into '
                f'"{self.target_game.title}"?\n\n'
                "The local-only library row will be removed, but the "
                "ROM file will remain on your computer."
            ),
            parent=self,
        )

        if not confirmed:
            return

        self.result_source_id = source_id
        self._close()

    def _cancel(self):
        self.result_source_id = None
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass

        self.destroy()

    def _centre_over_parent(self, parent):
        self.update_idletasks()
        parent.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        x = parent.winfo_rootx() + max(
            0,
            (parent.winfo_width() - width) // 2,
        )
        y = parent.winfo_rooty() + max(
            0,
            (parent.winfo_height() - height) // 2,
        )

        self.geometry(f"{width}x{height}+{x}+{y}")


def show_rom_merge_dialog(parent, target_game, candidates):
    """
    Opens the modal merge picker and returns the selected source ID.

    Returns None when the user cancels.
    """
    dialog = RomMergeDialog(
        parent=parent,
        target_game=target_game,
        candidates=candidates,
    )
    parent.wait_window(dialog)

    return dialog.result_source_id
