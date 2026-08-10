"""Left panel: connection settings + filters, in a scrollable container."""
import tkinter as tk
from tkinter import ttk

from .conn_form import ConnectionForm
from .filter_form import FilterForm


class LeftPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, width=360)
        self.app = app
        self.cfg = app.cfg
        self.pack_propagate(False)

        # Scrollable area: Canvas + inner Frame + vertical Scrollbar.
        self.canvas = tk.Canvas(self, highlightthickness=0, width=340, bd=0)
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = ttk.Frame(self.canvas, padding=(8, 4, 8, 8))
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_config)
        self.canvas.bind("<Configure>", self._on_canvas_config)
        self._bind_wheel()
        self._build()

    def _build(self):
        self.conn = ConnectionForm(self.inner, self.app)
        self.conn.pack(fill=tk.X)
        ttk.Separator(self.inner).pack(fill=tk.X, pady=8)
        self.filters = FilterForm(self.inner, self.app)
        self.filters.pack(fill=tk.X)

    def _on_inner_config(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_config(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def _bind_wheel(self):
        def on_wheel(e):
            delta = -1 if getattr(e, "delta", 0) > 0 or e.num == 4 else 1
            self.canvas.yview_scroll(delta, "units")
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(seq, on_wheel)
