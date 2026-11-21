from __future__ import annotations

from hashlib import sha256 as HashBytes
from tests.Convert.Solidworks.Research.Curve.Fields.AssertDigest import AssertDigest


# byte fields must expose verifiable metadata while keeping opaque payload bytes absent
def AssertBytes(Value: dict[str, object]) -> None:
    assert set(Value) == {"type", "bytes", "sha256", "context"}
    assert type(Value["bytes"]) is int
    assert Value["bytes"] >= 0
    ByteHash = AssertDigest(Value["sha256"])
    if Value["bytes"] == 0:
        assert ByteHash == HashBytes(b"").hexdigest()
