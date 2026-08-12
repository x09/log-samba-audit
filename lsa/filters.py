"""Client-side filtering of events (dates, types, statuses, query expressions)."""
from .model import SUCCESS_STATUSES
from .query import parse_query


class Filter:
    def __init__(self):
        self.date_from = None      # datetime or None
        self.date_to = None        # datetime or None
        self.types = set()         # empty = all
        self.statuses = set()      # empty = all; special: __success__/__failure__
        self.text = ""             # raw query string (for UI/config)
        self._predicate = None     # compiled query predicate

    def set_query(self, text):
        """Parse and store a search query. Raises ValueError on syntax error."""
        self.text = text.strip()
        self._predicate = parse_query(self.text)

    def accepts(self, ev):
        if self.date_from and ev.dt and ev.dt < self.date_from:
            return False
        if self.date_to and ev.dt and ev.dt > self.date_to:
            return False
        if self.types and ev.etype not in self.types:
            return False
        if self.statuses and not self._status_ok(ev):
            return False
        if self._predicate and not ev.matches_query(self._predicate):
            return False
        return True

    def _status_ok(self, ev):
        st = self.statuses
        if "__success__" in st and ev.is_success:
            return True
        if "__failure__" in st and ev.is_success is False:
            return True
        return ev.status in st
