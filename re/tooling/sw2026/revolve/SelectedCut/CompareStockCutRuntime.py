from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[5] / "src"), str(HERE.parents[2])]

from ComparePerpendicularRuntimes import differences, normalized
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


CONFIG = "Contents/Config-0"
VIEW_FIELDS = {"/fields/f368/f08/m0", "/fields/f368/f08/m4", "/fields/f368/f08/m8"}
MAC = "-0x1.0000000000000p-48"
WINDOWS = "-0x1.ffffffffffffep-49"


def compare_host_runtime(reference, guest):
    host, other = (SldprtArchive.from_bytes(data) for data in (reference, guest))
    if tuple(host.streams) != tuple(other.streams):
        raise ValueError("disclosed runtime changed stream topology")
    changed = set()
    for stream, before in host.streams.items():
        after = other.require(stream)
        if len(before) != len(after):
            raise ValueError("disclosed runtime changed logical stream length")
        if before != after:
            changed.add(stream)
    if changed - {CONFIG}:
        raise ValueError("disclosed runtime changed a stream outside Config-0")
    old, new = (normalized(ReadNativeLink(archive, 0).ConfigValue) for archive in (host, other))
    delta = differences(old, new)
    if not (
        (not changed and not delta)
        or (changed == {CONFIG} and len(delta) == 8
            and all(row["owner"]["class"] == "moView_c"
                    and row["path"][len(row["owner"]["path"]):] in VIEW_FIELDS
                    and (row["host_hex"], row["guest_hex"]) == (MAC, WINDOWS)
                    and row["ulp_distance"] == 2 for row in delta))
    ):
        raise ValueError("disclosed runtime differs outside the measured standard-view doubles")
    return {"host_sha256": sha256(reference).hexdigest(), "guest_sha256": sha256(guest).hexdigest(),
            "logical_stream_count": len(host.streams), "changed_streams": sorted(changed),
            "view_doubles": delta, "all_other_typed_fields_equal": True}
