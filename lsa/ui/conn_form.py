"""Connection settings form (gatewayd endpoint + TLS + units)."""
import tkinter as tk
from tkinter import ttk, filedialog


class ConnectionForm(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.cfg = app.cfg
        self.vars = {}
        self._inputs = []      # widgets disabled while connected
        self.connected = False
        self._build()

    def _row(self, parent, label, key, section="connection", width=22):
        fr = ttk.Frame(parent)
        fr.pack(fill=tk.X, pady=2)
        ttk.Label(fr, text=label, width=12, anchor=tk.W).pack(side=tk.LEFT)
        var = tk.StringVar(value=self.cfg.get(section, key))
        self.vars[key] = var
        e = ttk.Entry(fr, textvariable=var, width=width)
        e.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._inputs.append(e)
        return fr

    def _file_row(self, parent, label, key):
        fr = ttk.Frame(parent)
        fr.pack(fill=tk.X, pady=2)
        ttk.Label(fr, text=label, width=12, anchor=tk.W).pack(side=tk.LEFT)
        var = tk.StringVar(value=self.cfg.get("connection", key))
        self.vars[key] = var
        e = ttk.Entry(fr, textvariable=var)
        e.pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn = ttk.Button(fr, text="...", width=3,
                         command=lambda v=var: self._pick_file(v))
        btn.pack(side=tk.LEFT)
        self._inputs.extend([e, btn])
        return fr

    def _pick_file(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _build(self):
        ttk.Label(self, text=_("Connection"),
                  font=("", 11, "bold")).pack(anchor=tk.W)

        self._row(self, _("Host"), "host")
        self._row(self, _("Port"), "port", width=8)

        # Scheme selector
        fr = ttk.Frame(self)
        fr.pack(fill=tk.X, pady=2)
        ttk.Label(fr, text=_("Scheme"), width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.vars["scheme"] = tk.StringVar(value=self.cfg.get("connection", "scheme"))
        scheme_cb = ttk.Combobox(fr, textvariable=self.vars["scheme"], width=10,
                                 state="readonly", values=["http", "https"])
        scheme_cb.pack(side=tk.LEFT)
        self._inputs.append(scheme_cb)

        # TLS group
        self.tls = ttk.LabelFrame(self, text=_("TLS (https)"), padding=4)
        self.tls.pack(fill=tk.X, pady=4)
        self.vars["verify"] = tk.BooleanVar(
            value=self.cfg.getbool("connection", "verify", True))
        verify_cb = ttk.Checkbutton(self.tls, text=_("Verify server certificate"),
                                    variable=self.vars["verify"])
        verify_cb.pack(anchor=tk.W)
        self._inputs.append(verify_cb)
        self._file_row(self.tls, _("CA cert"), "ca_cert")
        self._file_row(self.tls, _("Client cert"), "client_cert")
        self._file_row(self.tls, _("Client key"), "client_key")

        self._row(self, _("Units"), "units")
        ttk.Label(self, text=_("comma-separated, e.g. samba.service, smbd.service"),
                  foreground="#888").pack(anchor=tk.W)

        self._row(self, _("Tail"), "tail_count", width=8)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=(6, 0))
        self.test_btn = ttk.Button(btns, text=_("Test"),
                                   command=self.app.on_test_connection)
        self.test_btn.pack(side=tk.LEFT)
        self._inputs.append(self.test_btn)
        self.connect_btn = ttk.Button(btns, text=_("Connect"),
                                      command=self.app.on_toggle_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=4)
        self.follow_var = tk.BooleanVar(value=False)
        self.follow_cb = ttk.Checkbutton(btns, text=_("Follow"),
                                         variable=self.follow_var,
                                         command=self.app.on_toggle_follow)
        self.follow_cb.pack(side=tk.LEFT, padx=4)
        self.follow_cb.state(["disabled"])  # only usable once connected

    def set_connected(self, connected):
        """Grey out connection fields and switch button label when connected."""
        self.connected = connected
        state = "disabled" if connected else "!disabled"
        for w in self._inputs:
            w.state([state])
        self.connect_btn.configure(
            text=_("Disconnect") if connected else _("Connect"))
        self.follow_cb.state(["!disabled"] if connected else ["disabled"])

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
