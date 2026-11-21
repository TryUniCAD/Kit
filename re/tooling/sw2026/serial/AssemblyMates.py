from __future__ import annotations

from Core import ArchiveError, DOCUMENT_VERSION_2026, Load, Obj, Store


def _mate_list_base(resolved_map, version):
    if version != DOCUMENT_VERSION_2026:
        raise ArchiveError(f"mate-list framing requires version {DOCUMENT_VERSION_2026}, got {version}")
    count = resolved_map.count
    if not 0 < count <= 0x7FFFFFFF:
        raise ArchiveError("resolved feature map count must fit the native mate-list prefix")
    return count


def load_mate_list(data, registry, version, *, resolved_map):
    count = _mate_list_base(resolved_map, version)
    archive = Load(data, count, registry, version, seed=resolved_map)
    prefix = archive.prim("i32")
    if prefix != count:
        raise ArchiveError(f"mate-list prefix {prefix} differs from resolved map count {count}")
    items = Obj("suObList")
    registry.run_load("suObList", archive, items.f, items)
    if archive.left():
        raise ArchiveError(f"mate list has {archive.left()} unread bytes")
    return tuple(row["o"] for row in items["items"]), archive


def store_mate_list(mates, registry, version, *, resolved_map):
    count = _mate_list_base(resolved_map, version)
    archive = Store(count, registry, version, seed=resolved_map)
    archive.prim("i32", count)
    rows = [{"o": mate} for mate in mates]
    items = Obj("suObList", {"n": len(rows), "items": rows})
    registry.run_store("suObList", archive, items.f, items)
    return bytes(archive.out)
