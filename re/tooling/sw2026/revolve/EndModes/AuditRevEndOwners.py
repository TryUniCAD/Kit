from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import MakePrismLines
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevProfile import ReadRevProfile
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevAxisRef import ReadRevAxisRef
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevFrame import ReadRevFrame
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners

VERSION = 19000


def digest(data):
    return sha256(data).hexdigest()


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def guard_runtime():
    blocked = []
    for encoding in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)

    def audit(event, _args):
        if event in ("open", "os.listdir", "os.scandir", "os.exec", "os.fork", "os.forkpty",
                     "os.system", "os.posix_spawn", "ctypes.dlopen") or event.startswith(
                         ("socket.", "subprocess.")):
            blocked.append(event)
            raise RuntimeError(f"revolve archive attempted external data access: {event}")

    sys.addaudithook(audit)
    return blocked


def point(position):
    return [position.x, position.y, position.z]


def angle_owner(link, value):
    if value is None:
        return None
    display = RequireNative(value, "moDisplayAngularDim_c")
    rows = NativeRows(display.FieldsValue["f850"])
    require(len(rows) == display.FieldsValue["n850"] == 1,
            "angular display did not own exactly one local handle")
    handle = RequireNative(rows[0]["o"], "moFeatureDimHandle_c")
    require(handle.FieldsValue["fe8"] is None and handle.FieldsValue["f100"] is None,
            "alternate angular dimension handle")
    dimension = RequireNative(handle.FieldsValue["ff0"], "AngleDim_c")
    parameter = RequireNative(dimension.FieldsValue["f28"], "moAngleParameter_c")
    fields = parameter.FieldsValue
    require(type(fields["f58"]) is float and fields["f68"] == 0
            and fields["f20"] == "" and fields["f48"] is None,
            "angle parameter uses alternate value or expression state")
    chain = (display, handle, dimension, parameter)
    return {
        "name": ReadNativeName(parameter), "radians": fields["f58"],
        "dimension_id": dimension.FieldsValue["f50"],
        "dimension_mode_words": {name: dimension.FieldsValue[name] for name in ("f30", "f54")},
        "owners": [dict(NativeNodeSpan(link, node)) for node in chain],
    }


def profile_frame(link, feature):
    (profile,) = ReadParents(feature)
    profile = RequireNative(profile, "moProfileFeature_c")
    axis = ReadRevAxisRef(feature, profile, link.ConfigValue.RootValue)
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    contour = ReadRevProfile(sketch, axis, link)
    reverse = feature.FieldsValue["f824"]
    require(type(reverse) is int and reverse in (0, 1), "unexpected direction byte")
    frame = ReadRevFrame(profile, link.ConfigValue.RootValue, IndexFeatures(link), contour, bool(reverse))
    loop = contour.LoopValue
    lines = MakePrismLines(loop)
    return {
        "profile": dict(NativeNodeSpan(link, profile)),
        "selected_axis_index": axis.IndexValue,
        "selected_axis_mark": axis.MarkValue,
        "raw_axis": point(frame.RawDirection),
        "effective_axis": point(frame.DirectionValue),
        "world_axis_start_mm": point(frame.StartValue),
        "world_axis_end_mm": point(frame.EndValue),
        "profile_basis": [point(basis) for basis in (frame.SupportValue.x_axis,
                          frame.SupportValue.y_axis, frame.SupportValue.z_axis)],
        "active_point_wire_ids": sorted(loop.PointsValue),
        "line_order_indexes": list(loop.OrderValue),
        "line_order_values_missing_from_point_domain": sorted(set(loop.OrderValue) - loop.PointsValue.keys()),
        "contour_lines_mm": [[[p.x, p.y] for p in (line.start, line.end)] for line in lines],
    }


def observe_ends(link, feature):
    fields = feature.FieldsValue
    end = RequireNative(fields["f8d8"], "moRevEndSpec_c")
    values = end.FieldsValue
    displays = {slot: angle_owner(link, values[slot]) for slot in ("f18", "f20")}
    numbers = [slot["owners"] for slot in displays.values() if slot is not None]
    if len(numbers) == 2:
        require(all((a["stream"], a["object_index"]) != (b["stream"], b["object_index"])
                    for a, b in zip(*numbers, strict=True)),
                "two angular branches alias a display, handle, dimension or parameter")
    return {
        "feature": dict(NativeNodeSpan(link, feature)), "feature_name": ReadNativeName(feature),
        "feature_words": {k: fields[k] for k in ("f820", "f824", "f828", "f870", "f8e8")},
        "feature_legacy_display_slots": {k: fields[k] is not None for k in ("f808", "f810")},
        "end": dict(NativeNodeSpan(link, end)),
        "end_words": {k: values[k] for k in ("f08", "f138", "f13c", "f0c", "f10",
                                            "f38", "f40", "f140", "f144")},
        "nonangle_slots_present": {k: values[k] is not None for k in ("f118", "f120", "f128", "f130", "f28", "f30")},
        "angles": displays,
    }


def audit_streams(archive, link):
    config, new_config = WriteConfigMut(link.ConfigValue.RootValue, VERSION, link.ConfigValue.HeaderValue)
    resolved, new_resolved = WriteResolMut(
        link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, VERSION,
        new_config.MapValue, link.ResolvedValue.ContextValue,
    )
    result = {}
    for name, payload, original, rewritten in (
        (link.ConfigName, config, link.ConfigValue, new_config),
        (link.StreamName, resolved, link.ResolvedValue, new_resolved),
    ):
        for graph in (original, rewritten):
            report = graph.ReportValue
            require(report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"],
                    f"{name} has unsupported bodies")
        require(archive.require(name) == payload, f"{name} does not re-emit identically")
        require(original.MapValue.CounterValue == rewritten.MapValue.CounterValue,
                f"{name} map counter changed")
        result[name] = {"sha256": digest(payload), "bytes": len(payload),
                        "map_counter": original.MapValue.CounterValue}
    return result


def inspect(raw):
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4, "unsupported container version")
    link = ReadNativeLink(archive, 0)
    roots = (node for node in link.ResolvedValue.RootsValue
             if isinstance(node, ArchiveNode) and node.ClassValue.NameValue == "moRevolution_c")
    (feature,) = roots
    row = observe_ends(link, feature)
    try:
        frame = profile_frame(link, feature)
    except (KeyError, ValueError, TypeError) as error:
        frame = {"refused": str(error)}
    try:
        ReadRevOwners(link)
    except (KeyError, ValueError, TypeError) as error:
        boundary = {"ordinary_owner_reader_refused": str(error)}
    else:
        boundary = {"ordinary_owner_reader_admitted": True}
    return row | boundary | {"profiles": frame, "streams": audit_streams(archive, link)}


def main():
    parser = ArgumentParser(description="Inspect one separately disclosed ordinary revolve source")
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    raw = args.asset.read_bytes()
    require(digest(raw) == args.sha256, "disclosed archive digest differs")
    blocked = guard_runtime()
    row = inspect(raw)
    require(not blocked, "the guarded archive attempted external access")
    print(json.dumps(row | {"source_sha256": args.sha256, "runtime_external_access_attempts": 0},
                     ensure_ascii=False, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
