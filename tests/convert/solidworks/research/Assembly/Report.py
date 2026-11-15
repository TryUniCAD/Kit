from __future__ import annotations

from builtins import getattr as GetAttr
from hashlib import sha256 as HashBytes
from typing import cast as CastValue


# native cstring decoding can preserve narrow encoding witnesses alongside ordinary unicode strings
def ReadText(Value: object) -> str:
    return CastValue(str, Value[1] if isinstance(Value, tuple) else Value)


# decoded graph observations expose allocation aliases and authored values lost at real archive boundaries
def InspectResult(
    ConfigValue: object, FileValue: object, OwnerValue: object, BlobValue: bytes
) -> dict[str, object]:
    Fields = GetAttr(ConfigValue, "f")
    FileFields = GetAttr(FileValue, "f")
    States = Fields["fce8"]
    DefaultState = States[0]["o"].f
    Profiles = [Fields["fc48"], Fields["fc50"], DefaultState["f08"]]
    return {
        "size": len(BlobValue),
        "hash": HashBytes(BlobValue).hexdigest(),
        "owner_identity": Fields["owner"] is OwnerValue,
        "name": ReadText(Fields["f18"].f["f08"]),
        "description": ReadText(Fields["f4a8"]),
        "local_id": Fields["f08"],
        "saved_version": Fields["f9a8"],
        "needs_update": bool(Fields["f0c"] & 1),
        "state_count": len(States),
        "componentless_default": DefaultState["f10"] is None,
        "distinct_profiles": len({id(ProfileValue) for ProfileValue in Profiles}),
        "profile_schemas": [ProfileValue.schema for ProfileValue in Profiles],
        "path": ReadText(FileFields["h18"].f["f08"]),
        "stem": ReadText(FileFields["h10"].f["f08"]),
        "category": FileFields["f20"],
        "created_at": FileFields["f28"],
        "configuration_schema": GetAttr(ConfigValue, "schema"),
        "file_schema": GetAttr(FileValue, "schema"),
    }
