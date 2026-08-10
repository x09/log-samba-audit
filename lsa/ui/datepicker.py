"""Simple calendar date picker widget (stdlib tkinter only, no tkcalendar)."""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar


class DatePicker(tk.Toplevel):
    """Modal calendar popup. On date selection, calls callback(datetime) and closes."""

    def __init__(self, parent, callback, initial=None):
        super().__init__(parent)
        self.callback = callback
        self.transient(parent)
        self.title(_("Select Date"))
        self.resizable(False, False)

        self.today = datetime.now().date()
        self.selected = (initial or self.today).replace(day=1)

        self._build()
        self.grab_set()
        self.focus_set()
        # Center over parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry("+%d+%d" % (x, y))

    def _build(self):
        # Header: month/year selector
        hdr = ttk.Frame(self)
        hdr.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(hdr, text="<", width=3, command=self._prev_month).pack(side=tk.LEFT)
        self.mon_year_var = tk.StringVar()
        ttk.Label(hdr, textvariable=self.mon_year_var, width=18,
                  anchor=tk.CENTER, font=("", 10, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(hdr, text=">", width=3, command=self._next_month).pack(side=tk.LEFT)

        # Weekday headers + day grid share ONE grid so columns align exactly.
        self.day_frame = ttk.Frame(self)
        self.day_frame.pack(padx=8, pady=(4, 8))
        for c in range(7):
            self.day_frame.columnconfigure(c, uniform="day")

        weekdays = [_("Mon"), _("Tue"), _("Wed"), _("Thu"),
                    _("Fri"), _("Sat"), _("Sun")]
        for c, wd in enumerate(weekdays):
            ttk.Label(self.day_frame, text=wd, width=3, anchor=tk.CENTER,
                      font=("", 8, "bold")).grid(row=0, column=c, padx=1, sticky="nsew")

        # Day buttons occupy rows 1..6 (grid row 0 is the header).
        self.day_btns = []
        for r in range(6):
            for c in range(7):
                btn = ttk.Button(self.day_frame, text="", width=3,
                                 command=lambda row=r, col=c: self._on_day(row, col))
                btn.grid(row=r + 1, column=c, padx=1, pady=1, sticky="nsew")
                self.day_btns.append(btn)

        self._render_month()

    def _render_month(self):
        y, m = self.selected.year, self.selected.month
        self.mon_year_var.set("%s %d" % (calendar.month_name[m], y))

        # Build the month grid
        cal = calendar.monthcalendar(y, m)
        # monthcalendar returns list of weeks (0 = day not in month)
        # pad to 6 weeks for consistent grid size
        while len(cal) < 6:
            cal.append([0] * 7)

        for idx, btn in enumerate(self.day_btns):
            row, col = divmod(idx, 7)
            day = cal[row][col] if row < len(cal) else 0
            if day == 0:
                btn.config(text="", state=tk.DISABLED)
            else:
                btn.config(text=str(day), state=tk.NORMAL)
                # Highlight today
                d = datetime(y, m, day).date()
                if d == self.today:
                    btn.config(style="Accent.TButton")
                else:
                    btn.config(style="TButton")

    def _prev_month(self):
        self.selected = (self.selected.replace(day=1) - timedelta(days=1)).replace(day=1)
        self._render_month()

    def _next_month(self):
        y, m = self.selected.year, self.selected.month
        if m == 12:
            self.selected = datetime(y + 1, 1, 1).date()
        else:
            self.selected = datetime(y, m + 1, 1).date()
        self._render_month()

    def _on_day(self, row, col):
        idx = row * 7 + col
        text = self.day_btns[idx].cget("text")
        if not text:
            return
        day = int(text)
        picked = datetime(self.selected.year, self.selected.month, day).date()
        self.callback(picked)
        self.destroy()