from __future__ import annotations

from re import fullmatch as MatchFull


# malformed fingerprints cannot bind inventory evidence to the actual input bytes
def AssertDigest(Value: object) -> str:
    assert isinstance(Value, str)
    assert MatchFull("[0-9a-f]{64}", Value) is not None
    return Value
