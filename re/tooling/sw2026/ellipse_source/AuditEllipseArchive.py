from argparse import ArgumentParser
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(ROOT / "src"), str(HERE.parent / "revolve/EndModes")]

from AuditRevEndOwners import guard_runtime
from EllipseArchiveCustody import BUILD, CODEC_BASELINE, MODEL_MODULE, SERIALIZE_MAP, SOURCE_LOCK, digest, load_disclosed, pinned
from EllipseArchiveGrammar import HANDLE, INLINE, observe_link, parse_link
from EllipseArchiveOwners import event_fields, read_owners
from ReplayEllipseArchive import replay
from EllipseModel import require
from EllipsePacket import ASSETS, CONTROLS
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

VERSION = 19000
CONFIG = "Contents/Config-0"
HEADER = CONFIG + "-ModelHeader"
RESOLVED = CONFIG + "-ResolvedFeatures"
CMGR = "Contents/CMgr"
PREWRITER = "e152ceab9e1738d85058e6bc85cb46422b64cf92104b3ad0ba4726bee172a43e"
PREWRITER_REVISION = "d3a1134c18027fa8a75676cf3cc7a8b9418395b3"


def first_stop(archive, mode, name, expected):
    with observe_link(mode) as events:
        try:
            ReadNativeLink(archive, 0)
        except BodyUnsupported as error:
            require(str(error) == expected, f"first owner stop changed: {error}")
            (record,) = events[name]
            return {"diagnostic": str(error), "wire": event_fields(record)}
    raise ValueError("the baseline unexpectedly read the full ellipse")


def stream_info(archive, name, report=None, mapping=None):
    data = archive.require(name)
    details = {"bytes": len(data), "sha256": digest(data)}
    if report is not None:
        require(report["completed"] and not report["missing_schemas"],
                f"{name} did not complete its typed traversal")
        details |= {"completed": True, "next_map_slot": mapping.CounterValue,
                    "byte_field_count": len(report["native_byte_fields"])}
    return details


def refusal(action, expected):
    try:
        action()
    except BodyUnsupported as error:
        require(str(error) == expected, f"unexpected ellipse refusal: {error}")
        return str(error)
    raise ValueError("alternate ellipse archive path was admitted")


def check_context(archive, link):
    resolved = link.ResolvedValue
    config = link.ConfigValue
    return refusal(
        lambda: ReadResolvedMut(archive.require(RESOLVED), VERSION, config.MapValue,
                                dict(resolved.ContextValue) | {"cmgr_f658": 0}, ReadEllipses=True),
        "unsupported ordinary SOLIDWORKS ellipse archive context",
    )


def check_control(data):
    archive = SldprtArchive.from_bytes(data)
    link = ReadNativeLink(archive, 0)
    return {"file_sha256": digest(data), "resolved_next_slot": link.ResolvedValue.MapValue.CounterValue,
            "typed_replay": replay(archive, link, ellipse=False),
            "opt_in_refusal": refusal(lambda: ReadNativeLink(archive, 0, ReadEllipses=True),
                                      "SOLIDWORKS ellipse archive requires one ellipse and one handle")}


def audit_case(case, enums):
    archive = SldprtArchive.from_bytes(case["raw"])
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "ellipse observation requires ordinary format 4 and version 19000")
    header = ReadHeaderGraph(archive.require(HEADER), VERSION)
    base = ReadConfigMut(archive.require(CONFIG), VERSION, header)
    current = first_stop(archive, "current", "handles",
                         "unsupported SOLIDWORKS body class sgEllipseHandle schema 1")
    handle = first_stop(archive, "handle", "inline",
                        "unsupported SOLIDWORKS body schema sk.sgEllipse.FUN_4c586da0")
    linked, events = parse_link(archive)
    config, resolved = linked.ConfigValue, linked.ResolvedValue
    seed = config.MapValue.EntriesValue
    require(base.MapValue.CounterValue == config.MapValue.CounterValue == resolved.MapBase
            and len(seed) == len(base.MapValue.EntriesValue)
            and all(earlier is later for earlier, later in zip(
                seed, resolved.MapValue.EntriesValue[:len(seed)], strict=True)),
            "resolved map did not carry the actual complete configuration prefix")
    return {
        "case": case["case"], "sha256": case["sha256"], "edited": case["edited"],
        "native_phase_pins": case["observation_pins"],
        "first_stops": {"shared_reader": current, "handle_only": handle},
        "streams": {CONFIG: stream_info(archive, CONFIG, config.ReportValue, config.MapValue),
                    HEADER: stream_info(archive, HEADER), CMGR: stream_info(archive, CMGR),
                    RESOLVED: stream_info(archive, RESOLVED, resolved.ReportValue, resolved.MapValue)},
        "context": dict(resolved.ContextValue), "inherited_map_entries": len(seed),
        "resolved_map_base": resolved.MapBase,
        "typed_replay": replay(archive, linked),
        "alternate_context_refusal": check_context(archive, linked),
        **read_owners(linked, events, case, enums),
    }


def group_sketches(rows):
    shared = []
    for row in rows:
        sketch = row.pop("sketch")
        points = sketch.pop("points")
        row["coordinates_m"] = {role: points[index]["coordinates_m"]
                                for role, index in sketch["point_bindings"].items()}
        sketch["points"] = [{key: value for key, value in point.items() if key != "coordinates_m"}
                            for point in points]
        row["geometry"] = {key: sketch.pop(key) for key in
                           ("center_m", "radii_m", "major_direction", "minor_direction",
                            "sketch_seam_cos_sin", "sketch_seam_phase_degrees")}
        shared.append(sketch)
    require(all(sketch == shared[0] for sketch in shared[1:]),
            "disclosed ellipse records differ in wire layout or identity")
    return shared[0]


def run(folder):
    lock, registered, cases = load_disclosed(folder)
    pinned(ROOT / "re/solidworks/measurements/2026/EllipseBlindBossPrewriterLock01.json", PREWRITER)
    controls = {name: pinned(ROOT / ASSETS / name, pin) for name, pin in sorted(CONTROLS.items())}
    dispatch = json.loads(pinned(ROOT / "re/data/Serialization/SerializeMap2026.json", SERIALIZE_MAP))
    classes = (HANDLE, "sgEntHandle", "sgEllipse", "sgSegment", "sgSketch")
    entries = {name: dispatch[name] for name in classes}
    require(entries[HANDLE]["serialize_addr"] == entries["sgEntHandle"]["serialize_addr"]
            and INLINE.endswith(entries["sgEllipse"]["serialize_addr"]),
            "the exact-build ellipse or handle dispatch disagrees with the observed grammar")
    blocked = guard_runtime()
    observed = [audit_case(case, registered["enums"]) for case in cases]
    control_replays = {name: check_control(data) for name, data in controls.items()}
    require(not blocked, "offline ellipse archive audit attempted an external access")
    return {
        "schema": "kit.sw2026.ellipse-blind-boss-linked-archive.v1",
        "codec_revision": CODEC_BASELINE, "oracle_build": BUILD, "disclosed_source_lock_sha256": SOURCE_LOCK,
        "disclosed_job_sha256": lock["job_sha256"], "registered_api_sha256": lock["registered_api_sha256"],
        "prewriter_lock_revision": PREWRITER_REVISION, "redacted_prewriter_lock_sha256": PREWRITER,
        "measured_source_processes": lock["distinct_processes"], "source_control_phases": len(lock["controls"]),
        "native_launches": 0, "runtime_external_accesses": len(blocked),
        "serialize_map_sha256": SERIALIZE_MAP, "model_module_sha256": MODEL_MODULE, "dispatch": entries,
        "format_version": 4, "archive_version": VERSION, "shared_sketch": group_sketches(observed),
        "cases": observed, "controls": control_replays,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Observe only the four checksum-locked disclosed ellipse source saves")
    parser.add_argument("--disclosed-root", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().disclosed_root), indent=2, sort_keys=True, allow_nan=False))
