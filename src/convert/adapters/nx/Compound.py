from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass


# malformed compound files need one stable adapter owned failure
class CompoundError(ValueError):
    __slots__ = ()


# compound directory entries need identity and tree links for path recovery
@DataClass(slots=True)
class CompoundEntry:
    index: int
    name: str
    kind: int
    left: int
    right: int
    child: int
    start: int
    size: int


# compound streams need one path and exact bounded payload for native replay
@DataClass(frozen=True, slots=True)
class CompoundStream:
    path: str
    data: bytes


# the parsed compound state stays inert so readers can split parsing responsibilities
@DataClass(slots=True)
class CompoundFile:
    data: bytes
    sector_size: int
    mini_size: int
    fat_count: int
    dir_start: int
    mini_cutoff: int
    minifat_start: int
    minifat_count: int
    difat_start: int
    difat_count: int
    fat: tuple[int, ...]
    entries: tuple[CompoundEntry, ...]
    minifat: tuple[int, ...]
    ministream: bytes
