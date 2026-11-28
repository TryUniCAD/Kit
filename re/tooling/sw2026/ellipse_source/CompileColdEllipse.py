from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
RESEARCH = HERE.parents[1]
sys.path[:0] = [str(path) for path in (ROOT, ROOT / "src", HERE.parent, RESEARCH / "edge_fillet_source")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(RESEARCH / "serial/defs")
sys.addaudithook(audit.InspectEvent)

from BuildColdEllipsePart import build, reflect
from ColdEllipseModel import make_document, FRONT
from EllipseArchiveGrammar import parse_link
from EllipseArchiveOwners import resolve_row
from EllipseModel import require
from ReplayEllipseArchive import replay
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors


def digest(raw):
    return sha256(raw).hexdigest()


blocked_external = []


def guard_external(event, _):
    if event.startswith(("socket.", "ctypes.", "winreg.")) or event in ("os.startfile", "os.startfile/2"):
        blocked_external.append(event)
        raise PermissionError("ellipse emitter requested an external dependency")


def refused(action, message):
    try:
        action()
    except ValueError as error:
        require(message in str(error), f"unexpected ellipse refusal: {error}")
    else:
        raise ValueError("missing ellipse scope or ownership refusal")


def inspect(plan, data, streams, config, resolved):
    archive = SldprtArchive.from_bytes(data)
    require(KPartitionStream not in archive.streams and len(streams) == len(archive.streams) == 10
            and all(archive.require(name) == value for name, value in streams.items()),
            "cold ellipse must carry exactly the fully generated ordinary streams and regenerate geometry")
    link, observed = parse_link(archive)
    exact = replay(archive, link)
    require((link.ConfigValue.MapValue.CounterValue, link.ResolvedValue.MapValue.CounterValue)
            == (config.MapValue.CounterValue, resolved.MapValue.CounterValue),
            "cold ellipse changed linked map frontiers in the actual reader")
    features = IndexFeatures(link)
    boss, = (node for node in features.values() if node.ClassValue.NameValue == "moExtrusion_c")
    extrusion = ReadExtrude(link, boss, features)
    profile = extrusion.ProfileValue
    reference = profile.FieldsValue["pd_f78"].FieldsValue["ff0"]
    support = features[reference["f00"]]
    frame = ReadPrismFrame(profile, link.ConfigValue.RootValue, features)
    basis = [tuple(getattr(value, axis) for axis in "xyz")
             for value in (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis)]
    require(support.ClassValue.NameValue == "moRefPlane_c" and ReadNativeName(support) == FRONT
            and ReadNativeName(profile) == plan.SketchName and ReadNativeName(boss) == plan.FeatureName
            and basis == [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
            and extrusion.ParentsValue == (profile,) and extrusion.ModeValue.value == "blind"
            and not extrusion.IsReversed and extrusion.SecondValue is None,
            "cold ellipse lost its actual bound support, sketch or forward blind boss")
    depth = extrusion.RequireDepth()
    require(depth.DepthValue.name == "D1" and depth.DepthValue.native_role == "driving"
            and depth.DepthValue.native_value == plan.DepthValue and depth.Dimension.FieldsValue["f50"] > 0,
            "cold ellipse lost its live D1 driver")
    sketch = profile.FieldsValue["pd_f80"]
    members = resolve_row(link, sketch, observed)
    points = {name: members["points"][index] for name, index in members["point_bindings"].items()}
    center, major, minor = plan.CenterValue, plan.MajorValue, plan.MinorValue
    expected = {"Center": center, "Seam": major, "Major": major, "Minor": minor,
                "OppositeMajor": reflect(center, major), "OppositeMinor": reflect(center, minor)}
    require(all(points[role]["coordinates_m"] == value for role, value in expected.items())
            and {role: point["value_fields"]["fe8"] for role, point in points.items()}
            == {role: (2 if role == "Seam" else 1) for role in points}
            and points["Seam"]["persistent_words"] != points["Major"]["persistent_words"]
            and points["Seam"]["value_fields"]["fe4"] == 2
            and points["Seam"]["handle_index"] == members["seam_handle"]["owner"]["object_index"],
            "separate two-use ellipse seam does not own the precise modeled major station")
    record = sketch.FieldsValue["ellipses"][0]["ellipse"]
    old = record["fcc_s"]
    try:
        record["fcc_s"] = members["point_bindings"]["Major"]
        refused(lambda: resolve_row(link, sketch, observed), "shared seam and five distinct short point ordinals")
    finally:
        record["fcc_s"] = old
    refused(lambda: ReadNativeLink(archive, 0), "unsupported SOLIDWORKS body class sgEllipseHandle schema 1")
    return {"linked_replays": exact, "root_count": len(link.ResolvedValue.RootsValue),
            "resolved_map_base": link.ResolvedValue.MapBase,
            "resolved_next_slot": link.ResolvedValue.MapValue.CounterValue,
            "point_bindings": members["point_bindings"], "points": list(points.values()),
            "seam_handle": members["seam_handle"], "depth_m": depth.DepthValue.native_value,
            "dimension_id": depth.Dimension.FieldsValue["f50"],
            "profile_id": profile.FieldsValue["f08"], "boss_id": boss.FieldsValue["f08"],
            "major_station": points["Seam"]["coordinates_m"], "all_points_m": expected,
            "refusals": ["crossed_endpoint", "ordinary_reader_closed"]}


def compile_request(wire):
    request = json.loads(wire)
    require(type(request) is dict and set(request) == {"model", "locator", "epoch"}, "expected exact neutral ellipse request")
    document = make_document(request["model"])
    plan, data, streams, config, resolved = build(document, request["locator"], request["epoch"])
    receipt = inspect(plan, data, streams, config, resolved)
    geometry = document.sketches[0].entities[0].geometry
    refused(lambda: build(make_document(request["model"] | {"radii_mm": [geometry.major_radius] * 2}),
                          request["locator"], request["epoch"]), "noncircular signed positive-depth calibration scope")
    shape = document.sketches[0]
    active = shape.entities[0]
    construction = replace(document, sketches=(replace(shape, entities=(replace(active, construction=True),)),))
    refused(lambda: build(construction, request["locator"], request["epoch"]), "free full closed entity")
    require(not audit.DeniedReads and not blocked_external, "guarded ellipse construction accessed external input")
    return {
        "input_sha256": digest(wire), "archive_sha256": digest(data), "bytes": len(data), "runtime_accesses": 0,
        "streams": {name: {"sha256": digest(value), "bytes": len(value)} for name, value in streams.items()},
        "locator": request["locator"], "ellipse": receipt,
        "refusals": receipt["refusals"] + ["equal_radii", "construction_entity"],
    }, data


if __name__ == "__main__":
    require(sys.argv[1:] in ([], ["--deliver"]), "ellipse worker accepts only stdin and optional delivery")
    sys.addaudithook(guard_external)
    tuple(lookup(name) for name in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"))
    audit.BeginBuild()
    wire = sys.stdin.buffer.read(65537)
    require(0 < len(wire) <= 65536, "expected bounded input on stdin")
    proof, archive = compile_request(wire)
    if sys.argv[1:]:
        proof["model_base64"] = b64encode(archive).decode("ascii")
    print(json.dumps(proof, sort_keys=True, allow_nan=False))
