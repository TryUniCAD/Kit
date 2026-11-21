from io import BytesIO
import json
from math import isclose

from AuditRevEndOwners import NativeNodeSpan, audit_streams, digest, require
from BuildThinPlanes import portable
from ThinPublicRead import check_projection, read_cold, tuple_close, vector

from convert import open_document
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyKernel import ReadBodyKernel
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadSavedThin import ReadSavedThin
from interchange.document.Behavior.DocumentIo import ToJson


def read_part(raw, brep):
    settings = {} if brep else {"include_brep": False, "include_tessellation": False}
    return open_document(BytesIO(raw), source_format="solidworks.sldprt", strict=True, **settings)


def measured_topology(topology, native):
    require((topology.solid_count, topology.shell_count, topology.valid) == (1, 1, True)
            and (topology.face_count, topology.edge_count, topology.vertex_count)
            == tuple(native[key] for key in ("faces", "edges", "vertices")),
            "neutral topology differs from actual native solid")
    for actual, expected in ((topology.volume, native["volume_m3"] * 1e9),
                             (topology.surface_area, native["area_m2"] * 1e6)):
        require(actual > 0 and f"{actual:.6g}" == f"{expected:.6g}", "solid measures differ at six significant figures")
    box = topology.bounding_box
    bounds = (*vector(box.minimum), *vector(box.maximum))
    require(all(isclose(actual, expected * 1000.0, rel_tol=1e-6, abs_tol=1e-9)
                for actual, expected in zip(bounds, native["bounds_m"], strict=True)), "native bounds differ")
    return {"faces": topology.face_count, "edges": topology.edge_count, "vertices": topology.vertex_count,
            "volume_mm3": topology.volume, "area_mm2": topology.surface_area, "bounds_mm": bounds}


def read_saved(raw, archive, link, native, case):
    semantic = read_part(raw, False)
    geometry = read_part(raw, True)
    check_projection(semantic, case, False)
    require(semantic.feature_timeline == geometry.feature_timeline and semantic.parameters == geometry.parameters
            and semantic.sketches == geometry.sketches and semantic.selections == geometry.selections,
            "physical and semantic modes disagree on editable history")
    owners = ReadSavedThin(link, archive, native["profile"]["configuration"])
    sweep = owners.SweepValue
    source_feature = sweep.NodeValue
    producer = f"sldprt:feature:{NativeNodeId(source_feature)}"
    feature, = (item for item in geometry.feature_timeline if item.id == producer)
    spans = {}
    for owner, measured in zip((sweep.EndValue.AlongValue, *owners.WallValues), native["drivers"].values(), strict=True):
        number = owner.RadiansValue if owner.NameValue == "D1" else owner.MetresValue
        require(measured["editable"] and measured["name"].split("@", 1)[0] == owner.NameValue
                and isclose(number * measured["display_scale"], measured["value"], rel_tol=1e-13, abs_tol=1e-15),
                "typed driver differs from its native editable value")
        spans[owner.NameValue] = NativeNodeSpan(link, owner.ParameterValue)
    public = tuple(item for item in geometry.parameters if item.owner_id == feature.id)
    require({item.name for item in public} == spans.keys()
            and all(item.attributes["typed_archive_owner"]["offset"] == spans[item.name]["offset"] for item in public),
            "public live parameter provenance is detached from the stored owner")
    native_tree = [(row["name"], row["type"], row["parent"]) for row in native["features"]]
    row, = [row for row in native["features"] if row["name"] == feature.name]
    support, = (plane for plane in geometry.support_planes if plane.id == geometry.sketches[0].support_plane_id)
    require(not row["error"] and not row["warning"] and not row["suppressed"]
            and tuple(native["parents"]) == (geometry.sketches[0].name, support.name), "native consumed profile differs")
    incident = native["definition"]["axis"]["points"]
    local_axis = geometry.sketches[0].entities[1].geometry
    require(tuple_close((local_axis.start.x, local_axis.start.y, local_axis.end.x, local_axis.end.y),
                        tuple(x * 1000.0 for point in incident for x in point[:2])), "actual native selected line differs")
    body, = geometry.bodies
    projected, = semantic.bodies
    require(body.id == projected.id and body.final_feature_id == projected.final_feature_id == producer
            and body.name == projected.name == native["measured"]["name"]
            and body.provenance == projected.provenance and body.topology == projected.topology,
            "two strict modes disagree on the actual native body")
    require(geometry.brep.bodies[0].design_body_id == body.id and len(geometry.brep.bodies) == 1
            and not geometry.brep.validate(frozenset((body.id,))) and not semantic.brep_payloads
            and not any(item.code == "sldprt.brep_reconstructed" for item in geometry.diagnostics)
            and geometry.metadata["solidworks.native_body_names"]["complete_brep_binding"]
            and not semantic.metadata["solidworks.native_body_names"]["complete_brep_binding"],
            "native body physical cache was replaced or incorrectly bound")
    stream = link.ConfigName + "-Partition"
    _, _, marks = ReadBodyKernel(archive.require(stream), stream)
    spec = source_feature.FieldsValue["f8f0"]
    radius = spec.FieldsValue["f48"]
    return {
        "kernel_marks": {"current": marks[0], "predecessor": marks[1]},
        "stored_thin_spec": NativeNodeSpan(link, spec),
        "saved_radial_display": NativeNodeSpan(link, radius) if radius is not None else None,
        "streams": audit_streams(archive, link), "parameters": spans,
        "native_tree_sha256": digest(json_bytes(native_tree)), "native_tree_rows": len(native_tree),
        "stored_body": dict(geometry.metadata["solidworks.native_body_names"]),
        "native_payloads": {item.kind: item.sha256 for item in geometry.brep_payloads},
        "strict_default_document_sha256": digest(ToJson(geometry).encode("utf-8")),
        "strict_semantic_document_sha256": digest(ToJson(semantic).encode("utf-8")),
        "measurements": measured_topology(body.topology, native["measured"]),
    }


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def assert_cold(candidate, case, locator, epoch, pin, root, gate, guard):
    before = guard["grammar_reads"]
    gate["enabled"] = True
    try:
        original = PrepareRevolve(portable(case), locator, epoch).BytesValue
        require(original == candidate and digest(original) == pin, "cold writer differs from the native-tested bytes")
        require(guard["grammar_reads"] == before, "cold writer read even the allowed reader grammar")
    finally:
        gate["enabled"] = False
    return {"candidate_sha256": pin, "writer_runtime_reads": 0, **read_cold(candidate, case, root / "src")}
