"""Custom tkinter widgets for ASMR Cleaner GUI."""

import tkinter as tk
from tkinter import ttk


class LabeledSlider(ttk.Frame):
    """A parameter row: label | scale | spinbox | unit | help button.

    The scale and spinbox are bidirectionally linked.
    """

    def __init__(self, parent, label_key, unit_key, tooltip_key,
                 from_, to, default, step, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self._step = step
        self._value = tk.DoubleVar(value=float(default))

        # Lazy import to avoid circular dependency with i18n
        from asmr_cleaner.i18n import t

        # Label
        self.label = ttk.Label(self, text=t(label_key) + ":", width=14, anchor="e")

        # Scale (slider)
        self.scale = ttk.Scale(
            self, from_=from_, to=to, variable=self._value,
            orient=tk.HORIZONTAL, command=self._on_scale_change
        )

        # Spinbox (numeric entry)
        self.spinbox = ttk.Spinbox(
            self, from_=from_, to=to, increment=step,
            textvariable=self._value, width=5
        )
        self.spinbox.bind("<Return>", self._on_spinbox_change)
        self.spinbox.bind("<FocusOut>", self._on_spinbox_change)

        # Unit label
        self.unit_label = ttk.Label(self, text=t(unit_key), width=4)

        # Help button
        self.help_btn = ttk.Label(self, text="?", cursor="hand2",
                                  foreground="gray", font=("", 9, "bold"))
        self.help_btn.bind("<Button-1>", lambda e: self._show_tooltip(t(tooltip_key)))

        # Layout
        self.label.pack(side=tk.LEFT, padx=(0, 2))
        self.scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.spinbox.pack(side=tk.LEFT, padx=2)
        self.unit_label.pack(side=tk.LEFT, padx=(0, 2))
        self.help_btn.pack(side=tk.LEFT)

    def get(self):
        """Return current value as float."""
        return self._value.get()

    def set(self, value):
        """Set value programmatically."""
        self._value.set(float(value))

    def _on_scale_change(self, event=None):
        """Called when slider moves — syncs spinbox and fires command."""
        val = self._value.get()
        if self._step:
            val = round(val / self._step) * self._step
        self._value.set(val)
        if self.command:
            self.command(val)

    def _on_spinbox_change(self, event=None):
        """Called when spinbox value changes — syncs slider and fires command."""
        try:
            val = float(self._value.get())
            if self.command:
                self.command(val)
        except (ValueError, tk.TclError):
            pass

    def _show_tooltip(self, text):
        """Show a simple tooltip popup near the help button."""
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{self.winfo_pointerx() + 15}+{self.winfo_pointery() + 10}")

        frame = ttk.Frame(tip, relief="solid", borderwidth=1, padding=8)
        frame.pack()
        lbl = ttk.Label(frame, text=text, justify=tk.LEFT, wraplength=300)
        lbl.pack()

        # Dismiss on click anywhere
        tip.bind("<Button-1>", lambda e: tip.destroy())
        tip.bind("<FocusOut>", lambda e: tip.destroy())
        # Auto-dismiss after 5 seconds
        tip.after(5000, tip.destroy)


class StageIndicator(ttk.Frame):
    """Horizontal stage indicator showing progress through processing stages."""

    STAGE_KEYS = ["stage.load", "stage.analyze", "stage.process",
                  "stage.export", "stage.log"]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        from asmr_cleaner.i18n import t

        self._base_labels = [t(key) for key in self.STAGE_KEYS]
        self._labels = []

        # Create labels with arrows between them
        inner = ttk.Frame(self)
        inner.pack(expand=True)

        for i, base_text in enumerate(self._base_labels):
            lbl = ttk.Label(inner, text=f"⬜ {base_text}", padding=(4, 2))
            lbl.pack(side=tk.LEFT)
            self._labels.append(lbl)

            if i < len(self.STAGE_KEYS) - 1:
                arrow = ttk.Label(inner, text="→", foreground="gray")
                arrow.pack(side=tk.LEFT, padx=2)

    def set_stage(self, stage_index):
        """Mark stage_index as current, all before as done, all after as pending.

        Args:
            stage_index: 0-based index (0=load, 1=analyze, 2=process, 3=export, 4=log)
        """
        for i, lbl in enumerate(self._labels):
            base = self._base_labels[i]
            if i < stage_index:
                lbl.configure(text=f"✅ {base}", foreground="green")
            elif i == stage_index:
                lbl.configure(text=f"🔄 {base}", foreground="blue")
            else:
                lbl.configure(text=f"⬜ {base}", foreground="gray")

    def set_all_done(self):
        """Mark all stages as complete."""
        for i, lbl in enumerate(self._labels):
            lbl.configure(text=f"✅ {self._base_labels[i]}", foreground="green")

    def reset(self):
        """Reset all stages to pending."""
        for i, lbl in enumerate(self._labels):
            lbl.configure(text=f"⬜ {self._base_labels[i]}", foreground="gray")
