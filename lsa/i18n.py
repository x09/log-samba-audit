"""gettext initialization. English is the default (source) language."""
import os
import gettext as _gettext

DOMAIN = "log-samba-audit"
_LOCALE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locale")

AVAILABLE = {"en": "English", "ru": "Русский"}
_current = "en"


def setup(language):
    """Install _() into builtins for the whole app."""
    global _current
    if language not in AVAILABLE:
        language = "en"
    _current = language
    try:
        tr = _gettext.translation(DOMAIN, _LOCALE_DIR, languages=[language], fallback=True)
    except OSError:
        tr = _gettext.NullTranslations()
    tr.install(names=["gettext", "ngettext"])


def current():
    return _current
