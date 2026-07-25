"""Log viewer dialog — displays formatted processing logs."""

import os
import tkinter as tk
from tkinter import ttk

from asmr_cleaner.i18n import t
from asmr_cleaner.log_writer import read_log, find_logs_for_file


def show_log_viewer(parent, log_path):
    """Open a dialog displaying the log at log_path."""
    try:
        data = read_log(log_path)
    except Exception:
        tk.messagebox.showerror(
            t("error.title"), t("error.decode_failed"))
        return

    _LogDialog(parent, data, log_path)


def show_log_selector(parent, input_path):
    """Find and display the most recent log for an input file.
    If multiple logs exist, let user choose."""
    logs = find_logs_for_file(input_path)

    if not logs:
        tk.messagebox.showinfo(t("info.title"), t("log.no_logs"))
        return

    if len(logs) == 1:
        show_log_viewer(parent, logs[0])
        return

    # Multiple logs — show selection dialog
    _LogSelectionDialog(parent, logs)


class _LogSelectionDialog(tk.Toplevel):
    """Dialog for selecting from multiple log files."""

    def __init__(self, parent, log_paths):
        super().__init__(parent)
        self.title(t("log.select_log"))
        self.log_paths = log_paths
        self.resizable(False, False)

        msg = ttk.Label(self, text=t("log.multiple_logs").format(len(log_paths)),
                        padding=10)
        msg.pack()

        list_frame = ttk.Frame(self)
        list_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, width=60, height=min(8, len(log_paths)))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                  command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        for path in log_paths:
            fname = os.path.basename(path)
            mtime = os.path.getmtime(path)
            import datetime
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.listbox.insert(tk.END, f"{dt}  —  {fname}")

        self.listbox.bind("<Double-Button-1>", self._on_select)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text=t("btn.close"), command=self.destroy).pack(
            side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="打开", command=self._on_select).pack(
            side=tk.RIGHT, padx=5)

        self.transient(parent)
        self.grab_set()

    def _on_select(self, event=None):
        sel = self.listbox.curselection()
        if sel:
            path = self.log_paths[sel[0]]
            self.destroy()
            show_log_viewer(self.master, path)


class _LogDialog(tk.Toplevel):
    """Formatted log display dialog."""

    def __init__(self, parent, data, log_path):
        super().__init__(parent)
        self.title(t("log.title"))
        self.data = data
        self.log_path = log_path
        self.resizable(True, True)
        self.minsize(500, 350)

        self._build()
        self.transient(parent)
        self.grab_set()

    def _build(self):
        data = self.data
        summary = data.get("summary", {})
        params = data.get("parameters", {})
        removed = data.get("removed_segments", [])
        input_info = data.get("input_info", {})

        # Top info frame
        info_frame = ttk.Frame(self, padding=10)
        info_frame.pack(fill=tk.X)

        rows = [
            (t("log.input_file"), os.path.basename(data.get("input_file", ""))),
            (t("log.output_file"), os.path.basename(data.get("output_file", ""))),
            (t("log.processed_at"), data.get("processed_at", "")[:19].replace("T", " ")),
            (t("log.original_duration"),
             _format_duration(summary.get("original_duration_sec", 0))),
            (t("log.output_duration"),
             _format_duration(summary.get("output_duration_sec", 0))),
            (t("log.reduction"),
             f"{summary.get('reduction_percent', 0):.1f}%"),
        ]

        for i, (label, value) in enumerate(rows):
            ttk.Label(info_frame, text=label + ":", font=("", 9, "bold")).grid(
                row=i, column=0, sticky="e", padx=(0, 5), pady=1)
            ttk.Label(info_frame, text=value).grid(
                row=i, column=1, sticky="w", pady=1)

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10)

        # Removed segments table
        if removed:
            total_count = len(removed)
            total_dur = _format_duration(sum(r["duration_sec"] for r in removed))

            table_header = ttk.Label(
                self,
                text=t("log.removed_header").format(total_count, total_dur),
                font=("", 9, "bold"), padding=5)
            table_header.pack(anchor="w", padx=10)

            # Table container with scrollbar
            table_frame = ttk.Frame(self, padding=5)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10)

            columns = ("#", "start", "end", "duration")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                height=min(len(removed), 12))
            tree.heading("#", text=t("log.col_index"))
            tree.heading("start", text=t("log.col_start"))
            tree.heading("end", text=t("log.col_end"))
            tree.heading("duration", text=t("log.col_duration"))

            tree.column("#", width=40, anchor="center")
            tree.column("start", width=120, anchor="center")
            tree.column("end", width=120, anchor="center")
            tree.column("duration", width=120, anchor="center")

            for r in removed:
                tree.insert("", tk.END, values=(
                    r["index"],
                    r["start_str"][:12],
                    r["end_str"][:12],
                    r["duration_str"],
                ))

            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                      command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Parameters at bottom
        param_text = t("log.params") + f": "
        param_text += f"{t('label.threshold')} {params.get('threshold_db', '?')}dB"
        param_text += f" | {t('label.min_silence')} {params.get('min_silence_sec', '?')}s"
        param_text += f" | {t('label.crossfade')} {params.get('crossfade_ms', '?')}ms"
        ttk.Label(self, text=param_text, padding=10).pack(anchor="w")

        # Bottom buttons
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text=t("btn.open_folder"),
                   command=self._open_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=t("btn.copy_text"),
                   command=self._copy_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=t("btn.close"),
                   command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _open_folder(self):
        """Open the folder containing the output file."""
        output_file = self.data.get("output_file", "")
        if output_file and os.path.exists(output_file):
            folder = os.path.dirname(output_file)
            os.startfile(folder)
        elif self.log_path and os.path.exists(self.log_path):
            os.startfile(os.path.dirname(self.log_path))

    def _copy_text(self):
        """Copy log summary to clipboard."""
        data = self.data
        summary = data.get("summary", {})
        lines = [
            f"{t('log.input_file')}: {os.path.basename(data.get('input_file', ''))}",
            f"{t('log.processed_at')}: {data.get('processed_at', '')[:19].replace('T', ' ')}",
            f"{t('log.original_duration')}: {_format_duration(summary.get('original_duration_sec', 0))}",
            f"{t('log.output_duration')}: {_format_duration(summary.get('output_duration_sec', 0))}",
            f"{t('log.reduction')}: {summary.get('reduction_percent', 0):.1f}%",
            f"\n{t('log.removed_header').format(summary.get('total_segments_removed', 0), _format_duration(summary.get('total_removed_sec', 0)))}:",
        ]
        for r in data.get("removed_segments", []):
            lines.append(
                f"  {r['index']}. {r['start_str']} → {r['end_str']} ({r['duration_str']})"
            )

        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        # Show brief confirmation
        self.after(100, lambda: None)  # Let clipboard settle


def _format_duration(seconds):
    """Format seconds as HH:MM:SS."""
    if seconds is None:
        return "—"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
