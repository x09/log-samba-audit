"""Normalized audit event parsed from a journald record."""
import json
from datetime import datetime, timezone

# Known Samba JSON audit event types (spec + observed on VM).
EVENT_TYPES = [
    "Authentication",
    "Authorization",
    "KDC Authorization",
    "dsdbChange",
    "passwordChange",
    "groupChange",
    "replicatedUpdate",
    "dsdbTransaction",
]

# Statuses meaning "success" across the two status families.
SUCCESS_STATUSES = {"NT_STATUS_OK", "Success"}


def _msg_to_str(msg):
    """journald MESSAGE may be a string or a list of byte ints."""
    if isinstance(msg, list):
        try:
            return bytes(b for b in msg if isinstance(b, int)).decode("utf-8", "replace")
        except (ValueError, TypeError):
            return str(msg)
    return msg or ""


def _parse_ts(value):
    """Parse Samba ISO timestamp like 2026-08-06T18:03:34.888357+0500."""
    if not value:
        return None
    v = value.strip()
    # Normalize +0500 -> +05:00 for fromisoformat on older pythons.
    if len(v) >= 5 and v[-5] in "+-" and v[-3] != ":":
        v = v[:-2] + ":" + v[-2:]
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None


class Event:
    """A single normalized audit event."""

    __slots__ = ("dt", "etype", "status", "status_code", "account",
                 "sid", "remote", "dn", "operation", "raw", "cursor", "message")

    def __init__(self, dt, etype, status, status_code, account, sid,
                 remote, dn, operation, raw, cursor, message):
        self.dt = dt
        self.etype = etype
        self.status = status
        self.status_code = status_code
        self.account = account
        self.sid = sid
        self.remote = remote
        self.dn = dn
        self.operation = operation
        self.raw = raw
        self.cursor = cursor
        self.message = message

    @property
    def is_success(self):
        if self.status is None:
            return None
        return self.status in SUCCESS_STATUSES

    def matches_text(self, needle):
        if not needle:
            return True
        return needle.lower() in self.message.lower()

    def time_str(self):
        if self.dt is None:
            return "?"
        return self.dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def parse_journald_record(rec):
    """Return an Event from a journald JSON record, or None if not audit JSON.

    Samba writes the audit payload into MESSAGE prefixed with whitespace,
    e.g. '  {"timestamp": ..., "type": "dsdbChange", ...}'.
    """
    message = _msg_to_str(rec.get("MESSAGE", ""))
    brace = message.find("{")
    if brace == -1:
        return None
    try:
        j = json.loads(message[brace:])
    except (ValueError, TypeError):
        return None
    etype = j.get("type")
    if not etype:
        return None

    body = j.get(etype)
    if not isinstance(body, dict):
        body = {}

    dt = _parse_ts(j.get("timestamp"))
    if dt is None:
        # Fall back to journald realtime (microseconds since epoch).
        rt = rec.get("__REALTIME_TIMESTAMP")
        if rt:
            try:
                dt = datetime.fromtimestamp(int(rt) / 1_000_000, tz=timezone.utc)
            except (ValueError, TypeError):
                dt = None

    return Event(
        dt=dt,
        etype=etype,
        status=body.get("status"),
        status_code=body.get("statusCode"),
        account=body.get("account"),
        sid=body.get("userSid") or body.get("sid"),
        remote=body.get("remoteAddress"),
        dn=body.get("dn") or body.get("group"),
        operation=body.get("operation") or body.get("action"),
        raw=j,
        cursor=rec.get("__CURSOR", ""),
        message=message[brace:],
    )
