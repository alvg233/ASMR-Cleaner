"""Main application window — central GUI assembly for ASMR Cleaner."""

import os
import gc
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from asmr_cleaner.i18n import t, set_language, get_language
from asmr_cleaner import settings
from asmr_cleaner.audio_io import get_audio_info, SUPPORTED_FORMATS
from asmr_cleaner.core import process

from gui.widgets import LabeledSlider, StageIndicator
from gui.file_info import FileInfoPanel
from gui.log_viewer import show_log_selector, show_log_viewer


class MainWindow(tk.Tk):
    """ASMR Cleaner main application window."""

    # 5-stage processing pipeline order, matching core.process() callback stage names
    _STAGE_MAP = {
        "load": 0,
        "analyze": 1,
        "process": 2,
        "export": 3,
        "log": 4,
    }

    _STAGE_STATUS_MAP = {
        "load": "status.loading",
        "analyze": "status.analyzing",
        "process": "status.processing",
        "export": "status.exporting",
        "log": "status.writing_log",
    }

    def __init__(self):
        super().__init__()

        # ── Load settings and apply saved language ──
        self._app_settings = settings.load()
        saved_lang = self._app_settings.get("language")
        if saved_lang:
            set_language(saved_lang)

        self.title(t("app.title"))
        self.minsize(800, 600)
        self.resizable(True, True)

        # ── Internal state ──
        self._input_path = None          # Currently selected input file
        self._processing = False          # True while worker thread is running
        self._progress_queue = queue.Queue()
        self._worker_thread = None
        self._log_path = None             # Path to the latest processing log

        # Configure ttk theme
        style = ttk.Style()
        style.theme_use("clam")

        # ── Build UI ──
        self._build_menu()
        self._build_input_frame()
        self._build_file_info()
        self._build_params_frame()
        self._build_buttons()
        self._build_stage_indicator()
        self._build_progress()
        self._build_statusbar()

        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start polling the progress queue (100 ms interval)
        self._poll_progress()

    # ──────────────────────────────────────────────
    # Menu
    # ──────────────────────────────────────────────

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.settings"), menu=settings_menu)

        lang_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=t("menu.language"), menu=lang_menu)

        self._lang_var = tk.StringVar(value=get_language())
        lang_menu.add_radiobutton(
            label="中文", value="zh",
            variable=self._lang_var,
            command=self._on_language_selected,
        )
        lang_menu.add_radiobutton(
            label="English", value="en",
            variable=self._lang_var,
            command=self._on_language_selected,
        )

        # ── Help menu ──
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.help"), menu=help_menu)
        help_menu.add_command(label=t("menu.guide"), command=self._show_help)
        help_menu.add_command(label=t("menu.about"), command=self._show_about)

    def _show_help(self):
        """Open the usage guide dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(t("help.title"))
        dialog.geometry("600x500")
        dialog.minsize(400, 300)
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(frame, wrap=tk.WORD, font=("Microsoft YaHei", 10),
                       padx=10, pady=10)
        text.insert("1.0", t("help.content"))
        text.configure(state="disabled")
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)

        ttk.Button(dialog, text=t("btn.close"), command=dialog.destroy).pack(pady=10)

    def _show_about(self):
        """Open the About dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(t("about.title"))
        dialog.geometry("400x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        content = t("about.content")
        lbl = ttk.Label(frame, text=content, justify=tk.CENTER, font=("", 10))
        lbl.pack(expand=True)

        ttk.Button(dialog, text=t("btn.close"), command=dialog.destroy).pack(pady=10)

    def _on_language_selected(self):
        """Handle language menu selection."""
        new_lang = self._lang_var.get()
        self._switch_language(new_lang)

    def _switch_language(self, lang):
        """Change language, persist setting, and notify user to restart."""
        set_language(lang)
        self._app_settings["language"] = lang
        settings.save(self._app_settings)
        messagebox.showinfo(
            t("info.title"),
            "Language changed. Please restart the application for full effect.\n\n"
            "语言已切换，请重启应用以完全生效。",
        )

    # ──────────────────────────────────────────────
    # Input File Frame
    # ──────────────────────────────────────────────

    def _build_input_frame(self):
        frame = ttk.LabelFrame(self, text=t("frame.input"), padding=10)
        frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._input_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self._input_var, state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(
            frame, text=t("btn.browse"), command=self._browse_file,
        )
        browse_btn.pack(side=tk.RIGHT)

    # ──────────────────────────────────────────────
    # File Info Panel
    # ──────────────────────────────────────────────

    def _build_file_info(self):
        self._file_info = FileInfoPanel(self, padding=10)
        self._file_info.pack(fill=tk.X, padx=10, pady=5)

    # ──────────────────────────────────────────────
    # Parameters Frame
    # ──────────────────────────────────────────────

    def _build_params_frame(self):
        frame = ttk.LabelFrame(self, text=t("frame.params"), padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Silence threshold: -90 to -20 dB
        self._threshold_slider = LabeledSlider(
            frame,
            label_key="label.threshold",
            unit_key="label.threshold_unit",
            tooltip_key="tooltip.threshold",
            from_=-90,
            to=-20,
            default=self._app_settings.get("default_threshold_db", -55),
            step=1,
        )
        self._threshold_slider.pack(fill=tk.X, pady=3)

        # Min silence duration: 0.5 to 60 seconds
        self._min_silence_slider = LabeledSlider(
            frame,
            label_key="label.min_silence",
            unit_key="label.min_silence_unit",
            tooltip_key="tooltip.min_silence",
            from_=0.5,
            to=60,
            default=self._app_settings.get("default_min_silence_sec", 5.0),
            step=0.5,
        )
        self._min_silence_slider.pack(fill=tk.X, pady=3)

        # Crossfade: 5 to 200 ms
        self._crossfade_slider = LabeledSlider(
            frame,
            label_key="label.crossfade",
            unit_key="label.crossfade_unit",
            tooltip_key="tooltip.crossfade",
            from_=5,
            to=200,
            default=self._app_settings.get("default_crossfade_ms", 30),
            step=5,
        )
        self._crossfade_slider.pack(fill=tk.X, pady=3)

        # Output format: FLAC (lossless compressed, default) or WAV
        fmt_frame = ttk.Frame(frame)
        fmt_frame.pack(fill=tk.X, pady=3)
        ttk.Label(fmt_frame, text=t("label.output_format") + ":", width=14,
                  anchor="e").pack(side=tk.LEFT, padx=(0, 2))
        self._format_var = tk.StringVar(value="flac")
        fmt_combo = ttk.Combobox(fmt_frame, textvariable=self._format_var,
                                 values=["flac", "wav"], state="readonly", width=6)
        fmt_combo.pack(side=tk.LEFT, padx=2)
        ttk.Label(fmt_frame, text=t("tooltip.output_format"),
                  foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=5)

    # ──────────────────────────────────────────────
    # Action Buttons
    # ──────────────────────────────────────────────

    def _build_buttons(self):
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X, padx=10)

        self._start_btn = ttk.Button(
            btn_frame,
            text=t("btn.start"),
            command=self._start_processing,
            state=tk.DISABLED,  # Disabled until a file is selected
        )
        self._start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._log_btn = ttk.Button(
            btn_frame,
            text=t("btn.view_log"),
            command=self._view_log,
        )
        self._log_btn.pack(side=tk.LEFT, padx=5)

    # ──────────────────────────────────────────────
    # Stage Indicator
    # ──────────────────────────────────────────────

    def _build_stage_indicator(self):
        self._stage_indicator = StageIndicator(self, padding=10)
        self._stage_indicator.pack(fill=tk.X, padx=10)

    # ──────────────────────────────────────────────
    # Progress Bar & Detail
    # ──────────────────────────────────────────────

    def _build_progress(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.X, padx=10)

        self._progress_bar = ttk.Progressbar(frame, mode="determinate", length=400)
        self._progress_bar.pack(fill=tk.X)

        self._progress_detail = ttk.Label(frame, text="", padding=(0, 5, 0, 0))
        self._progress_detail.pack(anchor="w")

    # ──────────────────────────────────────────────
    # Status Bar
    # ──────────────────────────────────────────────

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value=t("status.ready"))
        statusbar = ttk.Label(
            self,
            textvariable=self._status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    # ──────────────────────────────────────────────
    # File Selection
    # ──────────────────────────────────────────────

    def _browse_file(self):
        """Open the file selection dialog for audio files."""
        initial_dir = self._app_settings.get("last_input_dir") or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            title=t("frame.input"),
            initialdir=initial_dir,
            filetypes=[
                (
                    t("file_filter"),
                    " ".join(f"*{e.lower()}" for e in SUPPORTED_FORMATS),
                ),
                (t("file_filter_all"), "*.*"),
            ],
        )

        if not path:
            return

        self._input_path = path
        self._input_var.set(path)
        self._app_settings["last_input_dir"] = os.path.dirname(path)
        settings.save(self._app_settings)

        # Update file info panel
        self._file_info.show_file(path)

        # Enable the start button
        self._start_btn.configure(state=tk.NORMAL)
        self._status_var.set(t("status.select_file"))

    # ──────────────────────────────────────────────
    # Processing — Worker Thread & Queue
    # ──────────────────────────────────────────────

    def _start_processing(self):
        """Validate inputs and launch the worker thread."""
        if self._processing or not self._input_path:
            return

        # ── File size check (>2 GB warning) ──
        file_size = os.path.getsize(self._input_path)
        if file_size > 2 * 1024 * 1024 * 1024:
            ok = messagebox.askokcancel(
                t("error.large_file_title"),
                t("error.large_file").format(file_size / (1024**3)),
            )
            if not ok:
                return

        # ── Build output path ──
        base, ext = os.path.splitext(self._input_path)
        out_fmt = self._format_var.get()
        output_path = f"{base}_cleaned.{out_fmt}"

        # ── Overwrite check ──
        if os.path.exists(output_path):
            ok = messagebox.askokcancel(
                t("error.overwrite_title"),
                t("error.overwrite").format(output_path),
            )
            if not ok:
                return

        # ── Gather parameters from sliders ──
        params = {
            "threshold_db": float(self._threshold_slider.get()),
            "min_silence_sec": float(self._min_silence_slider.get()),
            "crossfade_ms": float(self._crossfade_slider.get()),
            "output_format": self._format_var.get(),
        }

        # ── Disable UI for the duration of processing ──
        self._processing = True
        self._start_btn.configure(text=t("btn.start.processing"), state=tk.DISABLED)
        self._stage_indicator.reset()
        self._progress_bar.configure(mode='indeterminate')
        self._progress_bar.start(20)  # animate while loading
        self._progress_detail.configure(text="")
        file_mb = os.path.getsize(self._input_path) / (1024 * 1024)
        self._status_var.set(
            t("status.loading") + f"  ({file_mb:.0f} MB)" if file_mb >= 1
            else t("status.loading"))

        # ── Start the background worker thread ──
        self._worker_thread = threading.Thread(
            target=self._worker_run,
            args=(self._input_path, output_path, params),
            daemon=True,
        )
        self._worker_thread.start()

    def _worker_run(self, input_path, output_path, params):
        """Background worker — runs process() and pushes progress to the queue.

        This method runs in a daemon thread and MUST NOT touch any tkinter
        widget directly.  All UI updates happen via _poll_progress() on the
        main thread.
        """
        try:

            def progress_cb(stage, frac, extra):
                self._progress_queue.put(("progress", stage, frac, extra))

            result = process(
                input_path,
                output_path,
                params["threshold_db"],
                params["min_silence_sec"],
                params["crossfade_ms"],
                progress_callback=progress_cb,
                output_format=params["output_format"],
            )
            self._progress_queue.put(("done", result))

        except Exception as e:
            self._progress_queue.put(("error", str(e)))

    def _poll_progress(self):
        """Poll the progress queue and update UI.  Called every 100 ms."""
        try:
            while True:
                msg = self._progress_queue.get_nowait()

                if msg[0] == "progress":
                    _, stage, frac, extra = msg
                    self._update_progress_ui(stage, frac, extra)

                elif msg[0] == "done":
                    result = msg[1]
                    self._on_processing_done(result)

                elif msg[0] == "error":
                    error_msg = msg[1]
                    self._on_processing_error(error_msg)

        except queue.Empty:
            pass

        self.after(100, self._poll_progress)

    # ──────────────────────────────────────────────
    # Progress UI Updates
    # ──────────────────────────────────────────────

    def _update_progress_ui(self, stage, frac, extra):
        """Update progress bar, stage indicator, and status text.

        Called on the main thread via _poll_progress().
        """
        # Switch from indeterminate to determinate on first real progress
        if self._progress_bar.cget('mode') == 'indeterminate':
            self._progress_bar.stop()
            self._progress_bar.configure(mode='determinate')

        # Stage indicator
        stage_idx = self._STAGE_MAP.get(stage, 0)
        self._stage_indicator.set_stage(stage_idx)

        # Progress bar
        self._progress_bar.configure(value=frac * 100)

        # Status text
        status_key = self._STAGE_STATUS_MAP.get(stage, "status.ready")
        self._status_var.set(t(status_key))

        # Detail text — show meaningful information per stage
        detail_parts = []

        if stage == "analyze":
            found = extra.get("found_segments", 0)
            total_removed = extra.get("total_removed", 0)

            if found > 0:
                detail_parts.append(
                    f"{t('progress.found_segments')}: {found} "
                    f"{t('progress.total_segments')} "
                    f"（{t('progress.total_duration')} "
                    f"{self._format_short_duration(total_removed)}）"
                )

        self._progress_detail.configure(text="  ".join(detail_parts))

    def _on_processing_done(self, result):
        """Called when processing completes successfully."""
        self._processing = False
        self._start_btn.configure(text=t("btn.start"), state=tk.NORMAL)
        self._stage_indicator.set_all_done()
        self._progress_bar.stop()
        self._progress_bar.configure(mode='determinate', value=100)

        summary = result["summary"]
        removed = result["removed_segments"]

        if len(removed) == 0:
            self._status_var.set(t("status.complete_no_silence"))
            self._progress_detail.configure(text="")

        elif summary.get("reduction_percent", 0) > 95:
            # Almost everything was silence — warn user
            messagebox.showwarning(
                t("error.all_silence_title"),
                t("error.all_silence").format(
                    100 - summary.get("reduction_percent", 0)
                ),
            )
            self._status_var.set(
                t("status.complete").format(result.get("log_path", ""))
            )

        else:
            self._status_var.set(
                t("status.complete").format(result.get("log_path", ""))
            )

            detail = t("status.complete_detail").format(
                segments=summary['total_segments_removed'],
                duration=self._format_short_duration(summary['total_removed_sec']),
                elapsed=result.get('elapsed_sec', 0),
            )
            self._progress_detail.configure(text=detail)

        self._log_path = result.get("log_path")
        gc.collect()

    def _on_processing_error(self, error_msg):
        """Called when processing fails."""
        self._processing = False
        self._start_btn.configure(text=t("btn.start"), state=tk.NORMAL)
        self._stage_indicator.reset()
        self._progress_bar.stop()
        self._progress_bar.configure(mode='determinate', value=0)
        self._progress_detail.configure(text="")
        self._status_var.set(t("status.ready"))

        messagebox.showerror(
            t("error.title"),
            t("error.processing").format(error_msg),
        )
        gc.collect()

    # ──────────────────────────────────────────────
    # Log Viewer
    # ──────────────────────────────────────────────

    def _view_log(self):
        """Open the log viewer for the current session / input file."""
        if self._log_path and os.path.exists(self._log_path):
            show_log_viewer(self, self._log_path)
        elif self._input_path:
            show_log_selector(self, self._input_path)
        else:
            messagebox.showinfo(t("info.title"), t("log.no_logs"))

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _format_short_duration(seconds):
        """Format seconds as a compact human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            m = int(seconds // 60)
            s = seconds % 60
            return f"{m}m {s:.0f}s"
        else:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}h {m}m"

    # ──────────────────────────────────────────────
    # Window Close Guard
    # ──────────────────────────────────────────────

    def _on_close(self):
        """Guard against closing while processing is active."""
        if self._processing:
            ok = messagebox.askokcancel(
                t("error.close_during_processing_title"),
                t("error.close_during_processing"),
            )
            if not ok:
                return
        self.destroy()
