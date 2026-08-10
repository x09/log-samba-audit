"""Network source: systemd-journal-gatewayd over HTTP/HTTPS.

Endpoint /entries with Accept: application/json returns newline-delimited
JSON records. Filtering by unit uses repeated _SYSTEMD_UNIT= params (OR).
Pagination via Range: entries=[cursor]:[skip]:[count]. Live tail via ?follow.
"""
import ssl
import json
import socket
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .base import LogSource, SourceError
from ..model import parse_journald_record


class NetworkSource(LogSource):
    def __init__(self, host, port, units, scheme="http", verify=True,
                 ca_cert="", client_cert="", client_key="", timeout=30,
                 follow_timeout=120):
        self.host = host
        self.port = int(port)
        self.scheme = scheme
        self.verify = verify
        self.ca_cert = ca_cert or None
        self.client_cert = client_cert or None
        self.client_key = client_key or None
        self.timeout = timeout
        self.follow_timeout = follow_timeout
        self.units = [u.strip() for u in units.split(",") if u.strip()]
        self._follow_resp = None      # open follow response, for cancellation
        self._cancelled = False

    def _ssl_context(self):
        if self.scheme != "https":
            return None
        ctx = ssl.create_default_context(cafile=self.ca_cert)
        if not self.verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if self.client_cert:
            ctx.load_cert_chain(certfile=self.client_cert,
                                keyfile=self.client_key or None)
        return ctx

    def _url(self, follow=False):
        params = []
        for u in self.units:
            params.append("_SYSTEMD_UNIT=" + quote(u))
        if follow:
            params.append("follow")
        query = "&".join(params)
        return "%s://%s:%d/entries?%s" % (self.scheme, self.host, self.port, query)

    def _open(self, url, range_header=None, timeout=None):
        req = Request(url)
        req.add_header("Accept", "application/json")
        if range_header:
            req.add_header("Range", range_header)
        ctx = self._ssl_context()
        try:
            return urlopen(req, timeout=timeout or self.timeout, context=ctx)
        except HTTPError as e:
            raise SourceError("HTTP %s: %s" % (e.code, e.reason))
        except (URLError, socket.timeout, OSError) as e:
            reason = getattr(e, "reason", e)
            raise SourceError(str(reason))

    def test_connection(self):
        """Return machine hostname string, or raise SourceError."""
        url = "%s://%s:%d/machine" % (self.scheme, self.host, self.port)
        resp = self._open(url)
        try:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        except (ValueError, OSError) as e:
            raise SourceError(str(e))
        finally:
            resp.close()
        return data.get("hostname", "?")

    def _read_batch(self, range_header):
        """Fetch one page. Returns (records, events, last_cursor, first_cursor)."""
        resp = self._open(self._url(follow=False), range_header=range_header)
        records = events = None
        events = []
        last_cursor = first_cursor = ""
        try:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                cur = rec.get("__CURSOR")
                if cur:
                    if not first_cursor:
                        first_cursor = cur
                    last_cursor = cur
                ev = parse_journald_record(rec)
                if ev is not None:
                    events.append(ev)
        finally:
            resp.close()
        return events, last_cursor, first_cursor

    def fetch_tail(self, count):
        """Load the last `count` matching entries. Returns (events, last_cursor)."""
        events, last_cursor, _first = self._read_batch(
            "entries=:-%d:%d" % (count, count))
        return events, last_cursor

    def scan_backward(self, accept, date_from=None, batch=500,
                      max_matches=50000, max_scanned=200000):
        """Page backward through the journal, collecting events where
        accept(ev) is True.

        Stops when: date_from is reached (oldest scanned < date_from), or the
        start of the journal is hit, or a safety cap fires (max_matches
        collected, or max_scanned entries examined). Returns
        (events_oldest_first, last_cursor, truncated).
        """
        _e, newest_cursor, _f = self._read_batch("entries=:-1:1")
        if not newest_cursor:
            return [], "", False
        last_cursor = newest_cursor
        collected = []
        seen = set()
        cursor = newest_cursor
        truncated = False
        scanned = 0
        oldest_dt = None
        while True:
            # `entries=CURSOR:-batch:batch` returns up to `batch` entries whose
            # window ends at CURSOR (oldest-first). We de-dup by cursor.
            evs, _last, first_cursor = self._read_batch(
                "entries=%s:-%d:%d" % (cursor, batch, batch))
            if not evs and not first_cursor:
                break  # reached start of journal
            new_in_batch = 0
            for ev in evs:
                if ev.cursor and ev.cursor in seen:
                    continue
                if ev.cursor:
                    seen.add(ev.cursor)
                new_in_batch += 1
                scanned += 1
                if ev.dt:
                    oldest_dt = ev.dt if oldest_dt is None else min(oldest_dt, ev.dt)
                if accept(ev):
                    collected.append(ev)
            if len(collected) >= max_matches or scanned >= max_scanned:
                truncated = True
                break
            if date_from and oldest_dt and oldest_dt < date_from:
                break  # covered the requested range
            if not first_cursor or new_in_batch == 0:
                break  # no progress -> start of journal
            cursor = first_cursor
        collected.sort(key=lambda e: (e.dt is None, e.dt))
        return collected, last_cursor, truncated

    def fetch_range(self, date_from, date_to, batch=500, max_events=50000):
        """Backward scan bounded to [date_from, date_to] (thin wrapper)."""
        def accept(ev):
            if date_to and ev.dt and ev.dt > date_to:
                return False
            if date_from and ev.dt and ev.dt < date_from:
                return False
            return True
        return self.scan_backward(accept, date_from=date_from, batch=batch,
                                  max_matches=max_events)

    @staticmethod
    def _resp_socket(resp):
        """Best-effort access to the raw socket behind a urllib response."""
        try:
            return resp.fp.raw._sock
        except AttributeError:
            return None

    def cancel(self):
        """Interrupt a running follow() from another thread.

        We shut the socket down (not close) so the blocked reader gets EOF and
        exits cleanly. Closing the response from here would race with the
        reader mid-read (AttributeError on fp) and could block the caller.
        """
        self._cancelled = True
        resp = self._follow_resp
        if resp is not None:
            sock = self._resp_socket(resp)
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def follow(self, last_cursor, on_event, should_stop):
        """Stream only new entries, resuming after idle timeouts / drops.

        A read timeout during follow just means "no new events for a while" —
        we reconnect from the last seen cursor (no gaps, no duplicates) instead
        of failing. Genuine HTTP errors (bad request/unreachable) are raised.
        """
        url = self._url(follow=True)
        self._cancelled = False

        while not self._cancelled and not should_stop():
            if last_cursor:
                # Resume just after the last seen cursor (skip 1, unbounded).
                range_header = "entries=%s:1:18446744073709551615" % last_cursor
            else:
                range_header = None
            try:
                resp = self._open(url, range_header=range_header,
                                  timeout=self.follow_timeout)
            except SourceError as e:
                # HTTP-level errors are fatal; transient ones are retried.
                if str(e).startswith("HTTP "):
                    raise
                if self._cancelled or should_stop():
                    return
                continue  # network hiccup — retry from same cursor
            self._follow_resp = resp
            try:
                for raw in resp:
                    if self._cancelled or should_stop():
                        return
                    line = raw.decode("utf-8", "replace").strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if rec.get("__CURSOR"):
                        last_cursor = rec["__CURSOR"]
                    ev = parse_journald_record(rec)
                    if ev is not None:
                        on_event(ev)
            except (socket.timeout, TimeoutError, URLError,
                    OSError, AttributeError):
                # Idle timeout, dropped connection, or a shutdown() from
                # cancel() landing mid-read: reconnect unless we're stopping.
                if self._cancelled or should_stop():
                    return
            finally:
                self._follow_resp = None
                try:
                    resp.close()
                except (OSError, AttributeError):
                    pass
