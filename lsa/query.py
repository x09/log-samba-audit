"""Query language parser using lark: logical operators, wildcards, grouping.

Syntax:
    term                   # simple substring match (case-insensitive)
    term1 & term2          # AND: both must match
    term1 | term2          # OR: at least one matches
    (term1 | term2) & term3  # grouping with parentheses
    user*                  # wildcard: * matches any chars, ? matches one char

Operator precedence: & binds tighter than | (like boolean algebra).
"""
import fnmatch
from lark import Lark, Transformer, LarkError


# EBNF grammar for search expressions.
_GRAMMAR = r"""
    ?expr: or_expr

    ?or_expr: and_expr
            | or_expr "|" and_expr  -> or_op

    ?and_expr: term
             | and_expr "&" term    -> and_op

    ?term: TERM                     -> term
         | "(" expr ")"

    TERM: /[^\s\(\)\|&]+/

    %import common.WS
    %ignore WS
"""

_parser = Lark(_GRAMMAR, start="expr", parser="lalr")


def _match_term(message, pattern):
    """Check if pattern (with optional wildcards) matches message.

    Both are compared case-insensitively. Supports * (any chars) and ? (one char).
    If the pattern contains no wildcards, it's treated as a substring search
    (equivalent to *pattern*).
    """
    # If no wildcard chars, treat as substring match.
    if "*" not in pattern and "?" not in pattern:
        return pattern.lower() in message.lower()
    # Otherwise use fnmatch for wildcard matching (case-insensitive).
    return fnmatch.fnmatch(message.lower(), pattern.lower())


class _PredicateBuilder(Transformer):
    """Transform the parse tree into a callable predicate.

    Each node returns a function that takes a message string and returns bool.
    """
    def term(self, items):
        pattern = str(items[0])
        return lambda msg: _match_term(msg, pattern)

    def and_op(self, items):
        left, right = items
        return lambda msg: left(msg) and right(msg)

    def or_op(self, items):
        left, right = items
        return lambda msg: left(msg) or right(msg)


def parse_query(text):
    """Parse a search query into a predicate function.

    Returns a callable that takes a message string and returns True if it matches.
    Raises ValueError if the syntax is invalid (with a user-friendly message).

    Examples:
        predicate = parse_query("user1 & admin")
        predicate("user1 logged in as admin")  # True
        predicate("user2 logged in")           # False
    """
    text = text.strip()
    if not text:
        # Empty query matches everything.
        return lambda msg: True
    try:
        tree = _parser.parse(text)
        predicate = _PredicateBuilder().transform(tree)
        return predicate
    except LarkError as e:
        # Simplify the error message for users.
        raise ValueError("Syntax error in search query: check operators & | and parentheses")
