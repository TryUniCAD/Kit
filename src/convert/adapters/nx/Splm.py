from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass


# modern nx container errors stay distinct from malformed object payloads
class SplmError(ValueError):
    __slots__ = ()


# the modern nx signature identifies splmsstr before directory parsing
KSplmMagic = b"SPLMSSTR"

# the supported splmsstr layout version remains six across observed nx releases
KSplmVersion = 6

# the absent footer offset states that the header directory is complete
KAbsentFooter = 0xFFFFFFFFFFFF

# the root storage uuid is stable across nx saved parts
KRootUuid = bytes.fromhex("611ec9b3fa60d1118ad90800362fb302")

# header entries name paths before the payload section
KHeaderRegion = "HEADER"

# footer entries carry the saved toggle information near end of file
KFooterRegion = "FOOTER"

# path lengths remain bounded by the splmsstr directory grammar
KMinPathBytes = 6

# path lengths remain bounded by the splmsstr directory grammar
KMaxPathBytes = 128


# one directory entry preserves the path payload and region for exact replay
@DataClass(frozen=True, slots=True)
class SplmEntry:
    path: str
    region: str
    data: bytes | None
    offset: int
    size: int


# the parsed splmsstr state stays inert so parsing and building remain separate
@DataClass(frozen=True, slots=True)
class SplmFile:
    data: bytes
    version: int
    file_tag: int
    footer_offset: int
    entries: tuple[SplmEntry, ...]
    fingerprint: bytes
    header_trailer: bytes
