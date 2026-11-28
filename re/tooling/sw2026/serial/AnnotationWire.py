from __future__ import annotations

from Core import ArchiveError
from Dsl import ver
from Schema import Fn


def require_19000(ar, scope, o):
    version = ver(ar)
    if version != 19000:
        raise ArchiveError(
            f"verified annotation wire layout requires version 19000, got {version}"
        )


def current_19000():
    return Fn(require_19000, require_19000)


def note_attachment_count(scope, ar):
    low = scope["n248"] & 0xFFFFFFFF
    return low if low < 0x80000000 else 0
