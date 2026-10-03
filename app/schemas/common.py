"""Validators every schema module shares, copied from `food`'s schema layer."""

import re
from urllib.parse import urlparse

# A scheme is letters followed by a colon - but not a colon followed by a
# digit, which is a port on a bare host (`localhost:8000`), not a scheme.
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:(?!\d)")


def normalise(value):
    """An empty form field is an absent value, not an empty string.

    Without this, clearing a name in the UI stores "" - which satisfies
    `num_nonnulls` and defeats `ck_note_has_a_name`.
    """
    if not isinstance(value, str):
        return value
    value = value.strip()
    return value or None


def not_null(value, message: str):
    """For a field that may be left out of a PATCH but not cleared: absent is
    never validated, so only an explicit null reaches this and is refused."""
    if value is None:
        raise ValueError(message)
    return value


def clean_aliases(values: list[str]) -> list[str]:
    """Trim, drop the empties, and refuse the same alias twice.

    Case-insensitive, because "Gesture" and "gesture" are one alias.
    """
    cleaned = [v.strip() for v in values if v and v.strip()]
    if len({v.casefold() for v in cleaned}) != len(cleaned):
        raise ValueError("The same alias is listed twice")
    return cleaned


def check_url(value: str) -> str:
    """http and https only. A javascript: URL rendered as a link is an XSS."""
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("A link must be an http or https URL")
    return value


def normalise_link(value):
    """What the owner typed, as a stored link.

    Anything without a scheme is taken as a web address and given `https://`.
    One WITH a scheme must be http or https.
    """
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        raise ValueError("A link needs a URL")
    if not _SCHEME.match(value):
        value = f"https://{value}"
    return check_url(value)
