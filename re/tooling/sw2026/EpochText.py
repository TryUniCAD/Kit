from __future__ import annotations

from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


def read_text(value, field, *, nonempty=False):
    if type(value) is CStringValue:
        text = value.TextValue
    elif type(value) is str:
        text = value
    else:
        raise ValueError("epoch typed text has an unsupported owner: " + field)
    if "\x00" in text or nonempty and not text:
        raise ValueError("epoch typed text is invalid: " + field)
    return text
