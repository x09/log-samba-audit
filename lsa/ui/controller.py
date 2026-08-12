"""Bridges a LogSource (worker threads) to the tkinter UI via a queue.

tkinter is single-threaded, so worker threads never touch widgets. They push
messages onto a Queue; the UI drains it periodically on the main thread.
"""
import queue
import threading

from ..sources.base import SourceError


class Controller:
    def __init__(self, root, on_message):
        self.root = root
        self._on_message = on_message          # called on main thread: (kind, payload)
        self.q = queue.Queue()
        self._stop = threading.Event()         # for follow
        self._scan_stop = threading.Event()    # for scan_backward
        self._follow_thread = None
        self._poll()

    def _poll(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                self._on_message(kind, payload)
        except queue.Empty:
            pass
        self.root.after(150, self._poll)

    def test_connection(self, source):
        def work():
            try:
                host = source.test_connection()
                self.q.put(("test_ok", host))
            except SourceError as e:
                self.q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def fetch_tail(self, source, count):
        def work():
            try:
                events, cursor = source.fetch_tail(count)
                self.q.put(("tail", (events, cursor)))
            except SourceError as e:
                self.q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def scan_backward(self, source, accept, date_from):
        self._scan_stop.clear()
        def work():
            try:
                events, cursor, truncated = source.scan_backward(
                    accept, date_from=date_from, check_stop=self._scan_stop.is_set)
                self.q.put(("range", (events, cursor, truncated)))
            except SourceError as e:
                self.q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def stop_scan(self):
        """Signal any running scan_backward to stop."""
        self._scan_stop.set()

    def start_follow(self, source, last_cursor):
        self.stop_follow()
        self._stop.clear()
        self._follow_source = source

        def work():
            try:
                source.follow(last_cursor,
                              lambda ev: self.q.put(("event", ev)),
                              self._stop.is_set)
            except SourceError as e:
                self.q.put(("error", str(e)))
            finally:
                self.q.put(("follow_stopped", None))

        self._follow_thread = threading.Thread(target=work, daemon=True)
        self._follow_thread.start()

    def stop_follow(self):
        self._stop.set()
        src = getattr(self, "_follow_source", None)
        if src is not None:
            try:
                src.cancel()
            except Exception:
                pass
            self._follow_source = None
        self._follow_thread = None

    def is_following(self):
        return self._follow_thread is not None and not self._stop.is_set()
