# Search Syntax in log-samba-audit-viewer

The "Search" field in the filters section supports logical expressions for flexible event searching.

## Basics

### Simple search (substring)
Without operators, a term is searched as a substring in the message (case-insensitive):
```
domainuser1         → finds "domainuser1", "DOMAINUSER1 logged", "CN=domainuser1,..."
administrator       → finds any event containing "administrator"
```

### Logical operators

**AND (`&`)** — both conditions must be met:
```
domainuser1 & administrator    → events containing BOTH "domainuser1" AND "administrator"
success & bind                 → successful bind events
```

**OR (`|`)** — at least one condition must be met:
```
user1 | user2 | admin          → events with any of these users
failed | error                 → events containing "failed" OR "error"
```

**Precedence:** `&` binds tighter than `|`. Query `a | b & c` reads as `a | (b & c)`.

### Grouping with parentheses

Use parentheses to change evaluation order:
```
(user1 | user2) & success      → (user1 OR user2) AND success
(domain* | admin*) & (ok | success)
```

### Wildcards

- `*` — any number of characters (including zero)
- `?` — exactly one character

**Examples:**
```
admin*              → starts with "admin": administrator, admin123
*admin              → ends with "admin": sysadmin, dbadmin
*user*              → contains "user": domainuser1, testuser, user
domain??            → domain + 2 chars: domain01, domainAB
```

⚠️ **Important:** wildcards match the **entire message string**, not individual words. For substring search without exact start/end, use a term without `*`.

## Real-world query examples

### Search by user
```
domainuser1                    # all events with this user
domain* & authenticated        # authentication of domain users
(admin* | root) & failed       # failed actions by admins or root
```

### Search by event type
```
bind | unbind                  # login/logout events
groupChange & (add | remove)   # group changes (add or remove)
```

### Search by status
```
success*                       # successful operations (NT_STATUS_OK, etc.)
*denied*                       # access denied
error | warning                # errors or warnings
```

### Complex queries
```
(user1 | user2) & (bind | unbind) & success
    → successful login/logout by user1 or user2

domain* & groupChange & !(success*)
    → group changes by domain users that are NOT successful
    (note: ! operator not yet implemented, use "Status" filter)

(192.168.1.* | 10.0.0.*) & failed
    → failed attempts from specific subnets
```

## Tips

1. **Start simple:** begin with a plain term, then add operators.
2. **Watch your parentheses:** unclosed parenthesis → error "check operators & | and parentheses".
3. **Case insensitive:** `User1`, `user1`, `USER1` — all the same.
4. **Prefix wildcard:** `admin*` is useful for finding all admin accounts.
5. **Use "Stop search" button** if the query takes long (searching for rare terms in large journals).

## Syntax errors

If the query is invalid, you'll see:
```
Syntax error in search query: check operators & | and parentheses
```

Common causes:
- Trailing operator: `user1 &`
- Leading operator: `| user1`
- Unclosed parenthesis: `(user1 | user2`
- Special characters without escaping: stick to letters and digits, avoid `#`, `@` inside terms

## Limitations

- Search runs **client-side** (application fetches events from server and filters locally).
- Searching for rare terms may take time — watch the status bar for progress.
- Maximum scanned events: 200,000 (protection against hanging).
- Search operates on the entire message text (MESSAGE from journald), not individual JSON fields.

---

**Feedback:** if you need additional operators (e.g. NOT `!`, field-specific search `account:user1`) — suggestions are welcome.
