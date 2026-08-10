"""Main application window: menu, two-panel layout, status bar."""
import os
import tkinter as tk
from tkinter import ttk, messagebox

from .. import i18n, __version__
from ..sources.network import NetworkSource
from .left_panel import LeftPanel
from .right_panel import RightPanel
from .controller import Controller
from .about import AboutDialog

PROJECT_URL = "https://github.com/x09/log-samba-audit"
ICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "icons")


class App:
    def __init__(self, cfg):
        self.cfg = cfg
        self.root = tk.Tk()
        self.root.title("log-samba-audit")
        self._set_window_icon()
        w = cfg.getint("ui", "window_width", 1100)
        h = cfg.getint("ui", "window_height", 680)
        self.root.geometry("%dx%d" % (w, h))
        self.root.minsize(800, 480)

        self._build_menu()
        self._build_body()
        self._build_statusbar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.last_cursor = ""
        self.controller = Controller(self.root, self._on_message)

    def _set_window_icon(self):
        """Set the title-bar / taskbar icon from icons/ (best-effort)."""
        self._icons = []  # keep refs so Tk doesn't garbage-collect them
        for sz in (256, 128, 64, 32):
            path = os.path.join(ICON_DIR, "log-samba-audit-%d.png" % sz)
            if os.path.exists(path):
                try:
                    self._icons.append(tk.PhotoImage(file=path))
                except tk.TclError:
                    pass
        if self._icons:
            try:
                self.root.iconphoto(True, *self._icons)
            except tk.TclError:
                pass

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label=_("Quit"), command=self._on_close)
        menubar.add_cascade(label=_("File"), menu=filem)

        langm = tk.Menu(menubar, tearoff=0)
        cur = i18n.current()
        for code, name in i18n.AVAILABLE.items():
            langm.add_radiobutton(
                label=name, value=code,
                variable=tk.StringVar(value=cur),
                command=lambda c=code: self._set_language(c))
        menubar.add_cascade(label=_("Language"), menu=langm)

        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(label=_("About"), command=self._about)
        menubar.add_cascade(label=_("Help"), menu=helpm)
        self.root.config(menu=menubar)

    def _build_body(self):
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        self.left = LeftPanel(self.paned, self)
        self.right = RightPanel(self.paned, self)
        self.paned.add(self.left, weight=0)
        self.paned.add(self.right, weight=1)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value=_("Ready"))
        bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(bar, textvariable=self.status_var, anchor=tk.W).pack(
            side=tk.LEFT, fill=tk.X, padx=6, pady=2)

    def set_status(self, text):
        self.status_var.set(text)

    def _set_language(self, code):
        self.cfg.set("ui", "language", code)
        self.cfg.save()
        messagebox.showinfo(
            _("Language"),
            _("The language will change after restarting the application."))

    def _about(self):
        AboutDialog(self.root, self._icons[-1] if self._icons else None)

    def _on_close(self):
        self.cfg.set("ui", "window_width", self.root.winfo_width())
        self.cfg.set("ui", "window_height", self.root.winfo_height())
        self.right.save_column_widths()
        self.cfg.save()
        self.root.destroy()

    # --- connection actions ---
    def _build_source(self):
        c = self.left.conn.collect()
        return NetworkSource(
            host=c["host"], port=c["port"], units=c["units"],
            scheme=c["scheme"], verify=c["verify"] in (True, "true", "True"),
            ca_cert=c["ca_cert"], client_cert=c["client_cert"],
            client_key=c["client_key"],
            follow_timeout=self.cfg.getint("connection", "follow_timeout", 120))

    def on_test_connection(self):
        self.set_status(_("Testing connection..."))
        self.controller.test_connection(self._build_source())

    def on_toggle_connect(self):
        if self.left.conn.connected:
            self.on_disconnect()
        else:
            self.on_connect()

    def on_connect(self):
        try:
            count = int(self.left.conn.vars["tail_count"].get())
        except ValueError:
            count = 500
        self._endpoint = "%s://%s:%s" % (
            self.left.conn.vars["scheme"].get(),
            self.left.conn.vars["host"].get(),
            self.left.conn.vars["port"].get())
        self._connecting = True
        self.left.conn.connect_btn.state(["disabled"])
        self.set_status(_("Connecting to %s...") % self._endpoint)
        self.controller.fetch_tail(self._build_source(), count)

    def on_disconnect(self):
        self.controller.stop_follow()
        self.left.conn.follow_var.set(False)
        self.left.conn.set_connected(False)
        self.set_status(_("Disconnected"))

    def on_toggle_follow(self):
        if self.left.conn.follow_var.get():
            self.set_status(_("Following new events..."))
            self.controller.start_follow(self._build_source(), self.last_cursor)
        else:
            self.controller.stop_follow()
            self.set_status(_("Follow stopped"))

    def _on_message(self, kind, payload):
        if kind == "test_ok":
            messagebox.showinfo(_("Test"),
                                _("Connected to: %s") % payload)
            self.set_status(_("Connection OK: %s") % payload)
        elif kind == "tail":
            events, cursor = payload
            self.last_cursor = cursor or self.last_cursor
            self.right.set_events(events)
            if getattr(self, "_connecting", False):
                self._connecting = False
                self.left.conn.connect_btn.state(["!disabled"])
                self.left.conn.set_connected(True)
            self.set_status(_("Connected to %s — %d events") %
                            (getattr(self, "_endpoint", "?"), len(events)))
        elif kind == "range":
            events, cursor, truncated = payload
            self.last_cursor = cursor or self.last_cursor
            self.right.set_events(events)
            if truncated:
                self.set_status(
                    _("Showing %d of %d events (limit reached — narrow the range)")
                    % (len(self.right.events), len(events)))
            else:
                self._report_shown()
        elif kind == "event":
            self.right.append_event(payload)
            if payload.cursor:
                self.last_cursor = payload.cursor
        elif kind == "error":
            if getattr(self, "_connecting", False):
                self._connecting = False
                self.left.conn.connect_btn.state(["!disabled"])
                self.left.conn.set_connected(False)
            messagebox.showerror(_("Error"), payload)
            self.set_status(_("Not connected — %s") % payload)
        elif kind == "follow_stopped":
            self.left.conn.follow_var.set(False)

    def on_apply_filter(self):
        try:
            f = self.left.filters.build_filter()
        except ValueError as bad:
            messagebox.showerror(_("Error"),
                                 _("Invalid date: %s") % bad)
            return
        self.right.filter = f
        # A text search or date range needs data from the server: client-side
        # filtering can only see the already-loaded tail. Scan the journal
        # backward for matches, then the same filter renders the result.
        if f.date_from or f.date_to or f.text:
            self.controller.stop_follow()
            self.left.conn.follow_var.set(False)
            if f.text:
                self.set_status(_("Searching the journal..."))
            else:
                self.set_status(_("Loading date range..."))
            self.controller.scan_backward(self._build_source(),
                                          f.accepts, f.date_from)
        else:
            self.right.set_filter(f)
            self._report_shown()

    def _report_shown(self):
        self.set_status(_("Showing %d of %d events") %
                        (len(self.right.tree.get_children()),
                         len(self.right.all_events)))

    def run(self):
        self.root.mainloop()
