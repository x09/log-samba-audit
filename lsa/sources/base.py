"""Common interface for log sources (network now, local later — see TODO.md)."""


class SourceError(Exception):
    """Raised on connection / read failures."""


class LogSource:
    """Base class. Subclasses read normalized Events from somewhere.

    Contract:
      fetch_tail(count) -> (list[Event], last_cursor)   # one-shot batch
      follow(last_cursor, on_event, should_stop)         # blocking loop,
          calls on_event(Event) for each new record until should_stop() is True
    """

    def fetch_tail(self, count):
        raise NotImplementedError

    def follow(self, last_cursor, on_event, should_stop):
        raise NotImplementedError
