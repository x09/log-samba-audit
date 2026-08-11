"""Connection settings form (gatewayd endpoint + TLS + units)."""
import os
import tkinter as tk
from tkinter import ttk, filedialog

_ICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "icons")


def _load_icon(name):
    path = os.path.join(_ICON_DIR, name)
    if os.path.exists(path):
        try:
            return tk.PhotoImage(file=path)
        except tk.TclError:
            return None
    return None


class ConnectionForm(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.cfg = app.cfg
        self.vars = {}
        self._inputs = []      # widgets disabled while connected
        self._tls_inputs = []  # TLS fields controlled by the Verify checkbox
        self.connected = False
        self._icons = {}       # keep PhotoImage refs alive
        self._build()

    def _entry_row(self, parent, label, key, width=22, section="connection"):
        fr = ttk.Frame(parent)
        fr.pack(fill=tk.X, pady=2)
        ttk.Label(fr, text=label, width=14, anchor=tk.W).pack(side=tk.LEFT)
        var = tk.StringVar(value=self.cfg.get(section, key))
        self.vars[key] = var
        e = ttk.Entry(fr, textvariable=var, width=width)
        e.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._inputs.append(e)
        return e

    def _file_row(self, parent, label, key, tls=False):
        fr = ttk.Frame(parent)
        fr.pack(fill=tk.X, pady=2)
        ttk.Label(fr, text=label, width=14, anchor=tk.W).pack(side=tk.LEFT)
        var = tk.StringVar(value=self.cfg.get("connection", key))
        self.vars[key] = var
        e = ttk.Entry(fr, textvariable=var)
        e.pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn = ttk.Button(fr, text="...", width=3,
                         command=lambda v=var: self._pick_file(v))
        btn.pack(side=tk.LEFT)
        self._inputs.extend([e, btn])
        if tls:
            self._tls_inputs.extend([e, btn])
        return e

    def _pick_file(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _build(self):
        # --- Network settings block: endpoint + TLS + Test button ---
        net = ttk.LabelFrame(self, text=_("Network settings"), padding=6)
        net.pack(fill=tk.X, pady=(0, 12))

        self._entry_row(net, _("Host"), "host")
        self._entry_row(net, _("Port"), "port", width=8)

        # Scheme selector
        scheme_fr = ttk.Frame(net)
        scheme_fr.pack(fill=tk.X, pady=2)
        ttk.Label(scheme_fr, text=_("Scheme"), width=14,
                  anchor=tk.W).pack(side=tk.LEFT)
        self.vars["scheme"] = tk.StringVar(value=self.cfg.get("connection", "scheme"))
        scheme_cb = ttk.Combobox(scheme_fr, textvariable=self.vars["scheme"],
                                 width=10, state="readonly",
                                 values=["http", "https"])
        scheme_cb.pack(side=tk.LEFT)
        self._inputs.append(scheme_cb)

        ttk.Separator(net).pack(fill=tk.X, pady=6)

        # TLS: verify checkbox gates the three certificate fields.
        self.vars["verify"] = tk.BooleanVar(
            value=self.cfg.getbool("connection", "verify", True))
        verify_cb = ttk.Checkbutton(
            net, text=_("Verify server certificate"),
            variable=self.vars["verify"], command=self._apply_tls_state)
        verify_cb.pack(anchor=tk.W)
        self._inputs.append(verify_cb)
        self._file_row(net, _("CA cert"), "ca_cert", tls=True)
        self._file_row(net, _("Client cert"), "client_cert", tls=True)
        self._file_row(net, _("Client key"), "client_key", tls=True)

        # Test button (with icon), inside the network block, left-aligned.
        self._icons["test"] = _load_icon("act-test.png")
        test_row = ttk.Frame(net)
        test_row.pack(fill=tk.X, pady=(6, 0))
        self.test_btn = ttk.Button(
            test_row, text=_("Test"), image=self._icons["test"],
            compound=tk.LEFT, command=self.app.on_test_connection)
        self.test_btn.pack(side=tk.LEFT)
        self._inputs.append(self.test_btn)

        # --- Units / tail (below the network block) ---
        self._entry_row(self, _("Units"), "units")
        ttk.Label(self, text=_("comma-separated, e.g. samba.service, smbd.service"),
                  foreground="#888").pack(anchor=tk.W)
        self._entry_row(self, _("Tail"), "tail_count", width=8)

        # --- Connect (right) + Follow (left) ---
        self._icons["connect"] = _load_icon("act-connect.png")
        self._icons["disconnect"] = _load_icon("act-disconnect.png")
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=(6, 0))
        self.follow_var = tk.BooleanVar(value=False)
        self.follow_cb = ttk.Checkbutton(btns, text=_("Follow"),
                                         variable=self.follow_var,
                                         command=self.app.on_toggle_follow)
        self.follow_cb.pack(side=tk.LEFT)
        self.follow_cb.state(["disabled"])  # only usable once connected
        self.connect_btn = ttk.Button(
            btns, text=_("Connect"), image=self._icons["connect"],
            compound=tk.LEFT, command=self.app.on_toggle_connect)
        self.connect_btn.pack(side=tk.RIGHT)

        self._apply_tls_state()

    def _apply_tls_state(self):
        """Enable the three TLS fields only when 'Verify' is checked."""
        if self.connected:
            return
        st = "!disabled" if self.vars["verify"].get() else "disabled"
        for w in self._tls_inputs:
            w.state([st])

    def set_connected(self, connected):
        """Grey out network fields and switch button label/icon when connected."""
        self.connected = connected
        state = "disabled" if connected else "!disabled"
        for w in self._inputs:
            w.state([state])
        icon = self._icons["disconnect"] if connected else self._icons["connect"]
        self.connect_btn.configure(
            text=_("Disconnect") if connected else _("Connect"), image=icon)
        self.follow_cb.state(["!disabled"] if connected else ["disabled"])
        self._apply_tls_state()  # honor Verify state after re-enabling

    def collect(self):
        """Read current field values into a dict and persist to config."""
        out = {}
        for key, var in self.vars.items():
            val = var.get()
            out[key] = val
            self.cfg.set("connection", key,
                         "true" if val is True else "false" if val is False else val)
        self.cfg.save()
        return out
