"""About dialog with a clickable project link (opens via xdg-open)."""
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk

from .. import __version__

PROJECT_URL = "https://github.com/x09/log-samba-audit"


def open_url(url):
    """Open a URL in the user's browser, preferring xdg-open on Linux."""
    try:
        subprocess.Popen(["xdg-open", url],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, ValueError):
        try:
            webbrowser.open(url)
        except webbrowser.Error:
            pass


class AboutDialog(tk.Toplevel):
    def __init__(self, master, icon=None):
        super().__init__(master)
        self.title(_("About"))
        self.resizable(False, False)
        self.transient(master)
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        if icon is not None:
            ttk.Label(frame, image=icon).pack(pady=(0, 10))

        ttk.Label(frame, text="log-samba-audit-viewer",
                  font=("", 14, "bold")).pack()
        ttk.Label(frame, text=_("Version %s") % __version__).pack()
        ttk.Label(frame, text=_("Samba AD JSON audit log viewer"),
                  foreground="#555").pack(pady=(2, 12))

        ttk.Label(frame, text=_("Project website:")).pack()
        link = ttk.Label(frame, text=PROJECT_URL, foreground="#1a5fb4",
                         cursor="hand2")
        link.pack()
        f = link.cget("font")
        link.configure(font=(f, 10, "underline") if isinstance(f, str) else f)
        link.bind("<Button-1>", lambda _e: open_url(PROJECT_URL))

        ttk.Button(frame, text=_("Close"),
                   command=self.destroy).pack(pady=(16, 0))

        self.update_idletasks()
        self._center(master)
        self.grab_set()

    def _center(self, master):
        try:
            mx, my = master.winfo_rootx(), master.winfo_rooty()
            mw, mh = master.winfo_width(), master.winfo_height()
            w, h = self.winfo_width(), self.winfo_height()
            self.geometry("+%d+%d" % (mx + (mw - w) // 2, my + (mh - h) // 2))
        except tk.TclError:
            pass
