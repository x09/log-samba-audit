"""Filter controls: text search, date range, event types, status mode."""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ..model import EVENT_TYPES


def _parse_dt(text, end=False):
    """Accept 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'; return aware local dt.

    When `end` is True and only a date is given, the value is treated as the
    end of that day (23:59:59.999999) so the 'To' bound is inclusive.
    """
    text = text.strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").astimezone()
    except ValueError:
        pass
    try:
        d = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise ValueError(text)
    if end:
        d = d.replace(hour=23, minute=59, second=59, microsecond=999999)
    return d.astimezone()


class FilterForm(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.cfg = app.cfg
        self.type_vars = {}
        self._build()

    def _build(self):
        ttk.Label(self, text=_("Filters"),
                  font=("", 11, "bold")).pack(anchor=tk.W)

        # Text search
        sfr = ttk.Frame(self)
        sfr.pack(fill=tk.X, pady=(4, 2))
        ttk.Label(sfr, text=_("Search"), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.search_var = tk.StringVar(value=self.cfg.get("filters", "search_text"))
        ttk.Entry(sfr, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True)

        # Date range with calendar buttons
        dfr = ttk.Frame(self)
        dfr.pack(fill=tk.X, pady=2)
        ttk.Label(dfr, text=_("From"), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.from_var = tk.StringVar()
        ttk.Entry(dfr, textvariable=self.from_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dfr, text="...", width=3,
                   command=lambda: self._pick_date(self.from_var)).pack(side=tk.LEFT)
        dfr2 = ttk.Frame(self)
        dfr2.pack(fill=tk.X, pady=2)
        ttk.Label(dfr2, text=_("To"), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.to_var = tk.StringVar()
        ttk.Entry(dfr2, textvariable=self.to_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dfr2, text="...", width=3,
                   command=lambda: self._pick_date(self.to_var)).pack(side=tk.LEFT)
        ttk.Label(self, text=_("date: YYYY-MM-DD [HH:MM:SS]"),
                  foreground="#888").pack(anchor=tk.W)

        # Status mode
        mfr = ttk.Frame(self)
        mfr.pack(fill=tk.X, pady=(6, 2))
        ttk.Label(mfr, text=_("Status"), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="all")
        # status combobox: internal values, shown via display map
        self._status_values = ["all", "success", "failure"]
        self._status_labels = {"all": _("all"), "success": _("success"),
                               "failure": _("failure")}
        cb = ttk.Combobox(mfr, textvariable=self.status_var, state="readonly",
                          width=14, values=[self._status_labels[v]
                                            for v in self._status_values])
        cb.current(0)
        cb.pack(side=tk.LEFT)
        self._status_cb = cb

        # Event types
        ttk.Label(self, text=_("Event types"),
                  font=("", 9, "bold")).pack(anchor=tk.W, pady=(8, 2))
        saved = [t for t in self.cfg.get("filters", "types").split(",") if t]
        for etype in EVENT_TYPES:
            v = tk.BooleanVar(value=(not saved) or (etype in saved))
            self.type_vars[etype] = v
            ttk.Checkbutton(self, text=etype, variable=v).pack(anchor=tk.W)

        # Buttons
        bfr = ttk.Frame(self)
        bfr.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(bfr, text=_("Apply"),
                   command=self.app.on_apply_filter).pack(side=tk.LEFT)
        ttk.Button(bfr, text=_("Reset"),
                   command=self._reset).pack(side=tk.LEFT, padx=4)

    def _pick_date(self, target_var):
        from .datepicker import DatePicker
        # Try to parse existing value as initial date, fallback to today.
        current = target_var.get().strip()
        initial = None
        if current:
            try:
                initial = _parse_dt(current).date()
            except ValueError:
                pass
        DatePicker(self, lambda d: target_var.set(d.strftime("%Y-%m-%d")), initial)

    def _reset(self):
        self.search_var.set("")
        self.from_var.set("")
        self.to_var.set("")
        self._status_cb.current(0)
        for v in self.type_vars.values():
            v.set(True)
        self.app.on_apply_filter()

    def build_filter(self):
        """Construct a Filter from current UI state. Raises ValueError on bad date."""
        from ..filters import Filter
        f = Filter()
        f.text = self.search_var.get().strip()
        f.date_from = _parse_dt(self.from_var.get())
        f.date_to = _parse_dt(self.to_var.get(), end=True)

        chosen = {t for t, v in self.type_vars.items() if v.get()}
        # empty set means "all"; only set when a real subset is selected
        if chosen and len(chosen) != len(self.type_vars):
            f.types = chosen

        # map display label back to internal status mode
        label = self.status_var.get()
        mode = next((v for v in self._status_values
                     if self._status_labels[v] == label), "all")
        if mode == "success":
            f.statuses = {"__success__"}
        elif mode == "failure":
            f.statuses = {"__failure__"}

        # persist
        self.cfg.set("filters", "search_text", f.text)
        self.cfg.set("filters", "types",
                     ",".join(sorted(chosen)) if chosen and
                     len(chosen) != len(self.type_vars) else "")
        self.cfg.save()
        return f
