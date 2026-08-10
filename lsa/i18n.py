"""gettext initialization. English is the default (source) language."""
import os
import gettext as _gettext

DOMAIN = "log-samba-audit"

# Locale files may live in one of several places depending on how the app is
# run/installed. We search these in order and use the first that actually
# contains a compiled catalog for the requested language:
#   1. bundled next to the app  (running from source, or RPM that ships
#      locale under /usr/share/<name>/locale)
#   2. the system standard dir  (RPM installing to /usr/share/locale)
_BUNDLED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locale")
_CANDIDATE_DIRS = [_BUNDLED_DIR, "/usr/share/locale", "/usr/local/share/locale"]

AVAILABLE = {"en": "English", "ru": "Русский"}
_current = "en"


def _find_locale_dir(language):
    """Return the first locale dir that has a catalog for `language`."""
    for d in _CANDIDATE_DIRS:
        if _gettext.find(DOMAIN, d, languages=[language]):
            return d
    return None


def setup(language):
    """Install _() into builtins for the whole app."""
    global _current
    if language not in AVAILABLE:
        language = "en"
    _current = language
    localedir = _find_locale_dir(language)
    # fallback=True -> NullTranslations (identity) when no catalog is found,
    # which is exactly what we want for English (the source language).
    tr = _gettext.translation(DOMAIN, localedir, languages=[language],
                              fallback=True)
    tr.install(names=["gettext", "ngettext"])


def current():
    return _current
