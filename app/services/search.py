"""The one LIKE pattern every search box builds, as `food`'s.

A search term is text the user typed, not a pattern: `%`, `_` and the escape
character itself are matched literally.
"""

ESCAPE = "\\"


def contains(q: str) -> str:
    """A LIKE pattern matching `q` anywhere, its wildcards escaped. Pass
    `escape=ESCAPE` to the `like` / `ilike` it is used in."""
    term = q.strip()
    for char in (ESCAPE, "%", "_"):
        term = term.replace(char, ESCAPE + char)
    return f"%{term}%"
