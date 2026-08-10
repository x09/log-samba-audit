#!/usr/bin/env python3
"""Entry point for log-samba-audit."""
import sys
import os

_CANDIDATE_DIRS = [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.dirname(os.path.realpath(__file__)),
    "/usr/share/log-samba-audit",
    "/usr/local/share/log-samba-audit",
    os.path.expanduser("~/.local/share/log-samba-audit"),
]

for _d in _CANDIDATE_DIRS:
    if os.path.isfile(os.path.join(_d, "lsa", "__init__.py")):
        if _d not in sys.path:
            sys.path.insert(0, _d)
        break


from lsa.config import Config
from lsa import i18n


def main():
    cfg = Config.load()
    i18n.setup(cfg.get("ui", "language", "en"))
    # Import UI after gettext is installed so _() is available in modules.
    from lsa.ui.app import App
    app = App(cfg)
    app.run()


if __name__ == "__main__":
    main()
