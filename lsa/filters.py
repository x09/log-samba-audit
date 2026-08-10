"""Client-side filtering of events (dates, types, statuses, text)."""
from .model import SUCCESS_STATUSES


class Filter:
    def __init__(self):
        self.date_from = None      # datetime or None
        self.date_to = None        # datetime or None
        self.types = set()         # empty = all
        self.statuses = set()      # empty = all; special: __success__/__failure__
        self.text = ""

    def accepts(self, ev):
        if self.date_from and ev.dt and ev.dt < self.date_from:
            return False
        if self.date_to and ev.dt and ev.dt > self.date_to:
            return False
        if self.types and ev.etype not in self.types:
            return False
        if self.statuses and not self._status_ok(ev):
            return False
        if self.text and not ev.matches_text(self.text):
            return False
        return True

    def _status_ok(self, ev):
        st = self.statuses
        if "__success__" in st and ev.is_success:
            return True
        if "__failure__" in st and ev.is_success is False:
            return True
        return ev.status in st
