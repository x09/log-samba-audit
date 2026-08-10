"""Application settings persisted to ~/.config/log-samba-audit.ini."""
import os
import configparser

CONFIG_PATH = os.path.expanduser("~/.config/log-samba-audit.ini")

DEFAULTS = {
    "ui": {
        "language": "en",
        "window_width": "1100",
        "window_height": "680",
        "sash_x": "360",
    },
    "connection": {
        "host": "192.168.150.10",
        "port": "19531",
        "scheme": "http",          # http | https
        "ca_cert": "",             # path to CA bundle (https)
        "client_cert": "",         # path to client cert (mutual TLS)
        "client_key": "",          # path to client key (mutual TLS)
        "verify": "true",          # verify server cert (https)
        "units": "samba.service",  # comma-separated systemd units
        "tail_count": "500",       # entries to load initially
        "follow_timeout": "120",   # follow: reconnect after N s of silence
    },
    "filters": {
        "search_text": "",
        "types": "",               # comma list; empty = all
        "statuses": "",            # comma list; empty = all
    },
    "table": {
        # column widths: key = column id, value = width in pixels
        # defaults set by UI if absent
    },
}


class Config:
    def __init__(self, parser):
        self._p = parser

    @classmethod
    def load(cls):
        p = configparser.ConfigParser()
        # seed defaults
        for section, values in DEFAULTS.items():
            p[section] = dict(values)
        if os.path.exists(CONFIG_PATH):
            try:
                p.read(CONFIG_PATH, encoding="utf-8")
            except (configparser.Error, OSError):
                pass
        # ensure all default keys exist even if file is partial
        for section, values in DEFAULTS.items():
            if not p.has_section(section):
                p.add_section(section)
            for k, v in values.items():
                if not p.has_option(section, k):
                    p.set(section, k, v)
        return cls(p)

    def get(self, section, key, fallback=""):
        return self._p.get(section, key, fallback=fallback)

    def getint(self, section, key, fallback=0):
        try:
            return self._p.getint(section, key, fallback=fallback)
        except ValueError:
            return fallback

    def getbool(self, section, key, fallback=False):
        try:
            return self._p.getboolean(section, key, fallback=fallback)
        except ValueError:
            return fallback

    def set(self, section, key, value):
        if not self._p.has_section(section):
            self._p.add_section(section)
        self._p.set(section, key, str(value))

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            self._p.write(f)
