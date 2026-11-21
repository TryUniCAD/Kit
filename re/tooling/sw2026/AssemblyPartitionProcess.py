from __future__ import annotations

import codecs
import json
import sys
from base64 import b64encode
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLING = ROOT / "re/tooling/sw2026"
for directory in (ROOT, ROOT / "src", TOOLING, TOOLING / "serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(TOOLING / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from builders.AssemblyDocument import construct_assembly_bundle
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodePartition, EncodeBrep, EncodePartition
import interchange.brep.Validation.BrepValidate
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
EXCLUDED = frozenset(("EncodeBlankApi", "EncodeBlankPart", "WriteSolidAttrs", "WriteBodySuffix"))
TRACKED = EXCLUDED | {"EncodeBrepModel", "EncodeBrepBody", "EmitBodiesMut", "EmitVendorMut", "EncodePartData", "DeriveBodyTree"}
MM_PER_M = 1000


def vector(value):
    return (value.x, value.y, value.z)


def point(node):
    return PlaneVector(*(node["pos"][axis] * MM_PER_M for axis in ("x", "y")))


def child_prism(child):
    profile, extrusion = child.profile, child.extrusion
    if (extrusion is None or extrusion.feature.cls != "moExtrusion_c" or extrusion.profile is not profile
            or extrusion.condition != "blind" or extrusion.reverse_direction or profile.arc_count
            or len(child.rectangle_dimensions) != 2 or profile.line_count != 4):
        raise ValueError("partition research requires one dimensioned Front rectangle with one forward blind boss")
    frame = profile.profile["_frame"]
    transform = Transform(
        SpaceVector(*(axis * MM_PER_M for axis in frame.origin)),
        SpaceVector(*frame.u), SpaceVector(*frame.v), SpaceVector(*frame.normal),
    )
    edges = tuple(LineGeometry(point(line["_start"]), point(line["_end"])) for line in profile.sketch["_line_nodes"])
    feature_id = extrusion.feature["f08"]
    sketch_id = profile.profile["f08"]
    body_id = f"prism-feature-{feature_id}"
    model, volume, area, bounds = BuildPrism(body_id, transform, edges, 0.0, extrusion.depth * MM_PER_M)
    return model, {
        "generated_body_id": model.bodies[0].id,
        "sketch_id": sketch_id, "extrusion_id": feature_id,
        "volume_mm3": volume, "area_mm2": area,
        "bounds_mm": (vector(bounds.minimum), vector(bounds.maximum)),
    }


def describe(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest(), "base64": b64encode(data).decode("ascii")}


def assemble(request):
    bundle = construct_assembly_bundle(registry=REGISTRY, request=request, include_xml_metadata=True)
    child = bundle.child
    if KPartitionStream in child.streams:
        raise ValueError("partition intervention requires a generated cache-free baseline")
    model, geometry = child_prism(child)
    calls = {}

    def observe(frame, event, unused):
        if event != "call" or frame.f_globals.get("__name__") != "convert.Geometry.Parasolid":
            return
        name = frame.f_code.co_name
        if name in EXCLUDED:
            raise RuntimeError(f"partition construction invoked excluded legacy path {name}")
        if name in TRACKED:
            calls[name] = calls.get(name, 0) + 1

    sys.setprofile(observe)
    try:
        payload = EncodeBrep(model, partition=True)
        partition = EncodePartition(payload)
    finally:
        sys.setprofile(None)
    decoded, = DecodePartition(partition, KPartitionStream)
    if decoded.data != payload or decoded.kind != "partition" or decoded.stored_size != len(partition):
        raise ValueError("partition wrapper did not round-trip one exact generated partition")
    parent = build_sldprt(bundle.assembly.streams)
    baseline = build_sldprt(child.streams)
    candidate = build_sldprt(child.streams | {KPartitionStream: partition})
    before = SldprtArchive.from_bytes(baseline).streams
    after = SldprtArchive.from_bytes(candidate).streams
    if set(after) - set(before) != {KPartitionStream} or any(after.get(name) != raw for name, raw in before.items()):
        raise ValueError("partition intervention changed existing child streams")
    return {
        "parent": describe(parent), "child_baseline": describe(baseline), "child_with_partition": describe(candidate),
        "partition": {"stream_name": KPartitionStream, "kind": decoded.kind, "schema": decoded.schema,
                      "decoded_bytes": len(payload), "decoded_sha256": decoded.sha256,
                      "bytes": len(partition), "sha256": sha256(partition).hexdigest()},
        "geometry": geometry, "encoding_calls": calls, "excluded_calls": sorted(EXCLUDED),
        "module_reads": AUDIT.ModuleReads, "denied_reads": AUDIT.DeniedReads,
    }


if __name__ == "__main__":
    request = json.load(sys.stdin)
    AUDIT.BeginBuild()
    print(json.dumps(assemble(request), allow_nan=False))
