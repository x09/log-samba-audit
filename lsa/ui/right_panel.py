"""Right panel: events table (top) + detail JSON view (bottom)."""
import csv
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..filters import Filter

COLUMNS = [
    ("time", "Time", 150),
    ("etype", "Type", 130),
    ("status", "Status", 170),
    ("account", "Account / SID", 200),
    ("remote", "Remote", 150),
    ("dn", "DN / Object", 260),
]


class RightPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=6)
        self.app = app
        self.events = []          # currently visible (filtered) rows
        self.all_events = []      # everything received, unfiltered
        self.filter = Filter()    # empty = accept all
        self._build()

    def filter_accepts(self, ev):
        return self.filter.accepts(ev)

    def set_filter(self, f):
        self.filter = f
        self._rebuild()

    def _rebuild(self):
        self.tree.delete(*self.tree.get_children())
        self.events = []
        for ev in self.all_events:
            if self.filter.accepts(ev):
                self.events.append(ev)
                self.tree.insert("", tk.END, values=self._row_values(ev),
                                 tags=(self._tag_for(ev),))
        self._scroll_bottom()

    def _build(self):
        vpaned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        vpaned.pack(fill=tk.BOTH, expand=True)
        vpaned.add(self._build_table(vpaned), weight=3)
        vpaned.add(self._build_detail(vpaned), weight=1)

    def _build_table(self, master):
        fr = ttk.Frame(master)
        cols = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(fr, columns=cols, show="headings",
                                 selectmode="extended")
        for key, title, default_width in COLUMNS:
            self.tree.heading(key, text=_(title))
            # restore width from config if present, else use default
            saved = self.app.cfg.get("table", key, "")
            width = int(saved) if saved else default_width
            self.tree.column(key, width=width, anchor=tk.W, stretch=False)
        ysb = ttk.Scrollbar(fr, orient=tk.VERTICAL, command=self.tree.yview)
        xsb = ttk.Scrollbar(fr, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        fr.rowconfigure(0, weight=1)
        fr.columnconfigure(0, weight=1)

        # Row highlight tags by outcome.
        self.tree.tag_configure("ok", foreground="#0a7d00")
        self.tree.tag_configure("fail", foreground="#c00000")
        self.tree.tag_configure("neutral", foreground="#333333")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-3>", self._on_right_click)
        self._build_context_menu()
        return fr

    def save_column_widths(self):
        """Persist current column widths to config."""
        for key, _title, _default in COLUMNS:
            w = self.tree.column(key, "width")
            self.app.cfg.set("table", key, str(w))

    def _build_detail(self, master):
        fr = ttk.Frame(master)
        self.detail = tk.Text(fr, height=8, wrap=tk.NONE, font=("monospace", 9))
        dsb = ttk.Scrollbar(fr, orient=tk.VERTICAL, command=self.detail.yview)
        self.detail.configure(yscrollcommand=dsb.set, state=tk.DISABLED)
        self.detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dsb.pack(side=tk.RIGHT, fill=tk.Y)
        return fr

    def _on_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.events):
            self._show_detail(self.events[idx])

    def _show_detail(self, ev):
        text = json.dumps(ev.raw, indent=2, ensure_ascii=False)
        self.detail.configure(state=tk.NORMAL)
        self.detail.delete("1.0", tk.END)
        self.detail.insert("1.0", text)
        self.detail.configure(state=tk.DISABLED)

    def _row_values(self, ev):
        return (ev.time_str(), ev.etype,
                ev.status if ev.status is not None else "",
                ev.account or ev.sid or "",
                ev.remote or "", ev.dn or "")

    def _tag_for(self, ev):
        ok = ev.is_success
        return "ok" if ok is True else "fail" if ok is False else "neutral"

    def set_events(self, events):
        """Store full list (after a tail fetch) and render filtered rows."""
        self.all_events = list(events)
        self._rebuild()

    def append_event(self, ev):
        """Add one event (used by follow); render only if it passes the filter."""
        self.all_events.append(ev)
        if self.filter.accepts(ev):
            self.events.append(ev)
            self.tree.insert("", tk.END, values=self._row_values(ev),
                             tags=(self._tag_for(ev),))
            self._scroll_bottom()

    def _scroll_bottom(self):
        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])

    def _build_context_menu(self):
        """Create the right-click context menu for export."""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label=_("Export selected..."),
                                      command=self.export_selected)

    def _on_right_click(self, event):
        """Show context menu if there's a selection."""
        sel = self.tree.selection()
        if not sel:
            return
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def export_selected(self):
        """Export selected rows to TSV with tab-separated columns + full JSON."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(_("Export"), _("No rows selected."))
            return
        # Map item IDs to event indices.
        indices = [self.tree.index(iid) for iid in sel]
        selected_events = [self.events[i] for i in indices if 0 <= i < len(self.events)]
        if not selected_events:
            messagebox.showinfo(_("Export"), _("No valid events to export."))
            return
        # Ask for save location.
        path = filedialog.asksaveasfilename(
            title=_("Export to TSV"),
            defaultextension=".tsv",
            filetypes=[(_("TSV (Tab-separated)"), "*.tsv"), (_("All files"), "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL,
                                    lineterminator="\n")
                # Header row.
                writer.writerow([_("Time"), _("Type"), _("Status"),
                                 _("Account / SID"), _("Remote"), _("DN / Object"),
                                 _("Data")])
                # Data rows.
                for ev in selected_events:
                    writer.writerow([
                        ev.time_str(),
                        ev.etype,
                        ev.status if ev.status is not None else "",
                        ev.account or ev.sid or "",
                        ev.remote or "",
                        ev.dn or "",
                        json.dumps(ev.raw, ensure_ascii=False, separators=(',', ':'))
                    ])
            messagebox.showinfo(_("Export"),
                                _("Exported %d records to %s") % (len(selected_events), path))
        except OSError as e:
            messagebox.showerror(_("Error"), _("Export failed: %s") % e)
