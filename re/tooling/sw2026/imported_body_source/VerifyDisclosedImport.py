from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import platform
import sys
import zlib

from convert.Geometry.Parasolid import DecodePartData, EncodePartData
from para.Partition import SCHEMAS
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

from BuildLocalBodyKernel import make_nodes, boundary_measures, require_closed_unattributed
from LocalBodyKernel import EDGE, FACE, VERTEX, _render_local, decode_local, fingerprint, require
from ProjectDisclosedImport import coordinates, decode_import, project_import


ROOT = Path(__file__).resolve().parents[4]
DISCLOSED = {
    "DisclosedImported": (
        "ImportedBodySourceDisclosed03/DisclosedImported.SLDPRT",
        "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325",
    ),
    "OtherShape": (
        "ImportedBodyContrast02/OtherShape.SLDPRT",
        "8c77ddcd2451466781ae153b7724808f4e9bbf102ebd14aab6cd6b9274870f1d",
    ),
    "RenamedFeature": (
        "ImportedBodyContrast02/RenamedFeature.SLDPRT",
        "660277a250a8c719705d6332cfc1f3713ccc5082d07de2ad5c3006279c1f20e8",
    ),
    "RenamedBody": (
        "ImportedBodyContrast02/RenamedBody.SLDPRT",
        "2814fd13c29c840f2079485d47856333e756860fd0abee927703fc47a7cb7f43",
    ),
    "Control": (
        "ImportedBodyContrast02/Control.SLDPRT",
        "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57",
    ),
}
OWNING_SOURCES = (
    "re/tooling/sw2026/imported_body_source/ProjectDisclosedImport.py",
    "re/tooling/sw2026/imported_body_source/VerifyDisclosedImport.py",
    "re/tooling/sw2026/imported_body_source/BuildLocalBodyKernel.py",
    "re/tooling/sw2026/imported_body_source/LocalBodyKernel.py",
    "src/convert/Geometry/Extrude/Polygon/PolygonExtrude.py",
    "src/convert/adapters/solidworks/Core/Adapter.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Presentation/NativeRow.py",
    "tests/Convert/Solidworks/Research/ConstructionGuard.py",
)


def load_documents(packet):
    documents = {}
    for key, (relative, digest) in DISCLOSED.items():
        raw = (packet / relative).read_bytes()
        require(sha256(raw).hexdigest() == digest, "disclosed source SHA-256 mismatch for " + key)
        documents[key] = decode_import(raw)
    return documents


def analytic_measures(model):
    axes = tuple(zip(*(coordinates(vertex.point) for vertex in model.vertices), strict=True))
    lower, upper = tuple(min(axis) for axis in axes), tuple(max(axis) for axis in axes)
    x, y, z = (end - start for start, end in zip(lower, upper, strict=True))
    return {
        "volume_m3": x * y * z / 1e9,
        "area_m2": 2 * (x * y + y * z + z * x) / 1e6,
        "centroid_m": tuple((start + end) / 2000 for start, end in zip(lower, upper, strict=True)),
        "bounds_m": tuple(tuple(value / 1000 for value in limit) for limit in (lower, upper)),
    }


def without_payloads(document):
    model = document.brep
    collections = (
        "curves", "surfaces", "vertices", "edges", "coedges", "loops", "faces",
        "face_uses", "shells", "shell_uses", "regions", "bodies",
    )
    geometry = replace(model, **{
        name: tuple(replace(item, attributes={}, provenance=None) for item in getattr(model, name))
        for name in collections
    })
    feature_attributes = ("native_type", "native_object_id", "typed_archive_owner")
    owner_fields = ("native_class", "native_stream", "native_object_id", "properties")
    features = tuple(
        replace(row, provenance=None,
                attributes={key: row.attributes[key] for key in feature_attributes if key in row.attributes},
                definition=replace(
                    row.definition, object_data={
                        key: row.definition.object_data[key] for key in owner_fields if key in row.definition.object_data
                    },
                ))
        for row in document.feature_timeline
    )
    return replace(
        document, brep=geometry, brep_payloads=(), meshes=(), materials=(),
        metadata={"solidworks.typed_configuration_manager": document.metadata["solidworks.typed_configuration_manager"]},
        bodies=tuple(replace(body, attributes={}, provenance=None, material_id=None) for body in document.bodies),
        feature_timeline=features,
    )


def check_positive(document):
    result = project_import(document)
    without_source_bytes = project_import(without_payloads(document))
    require(result.model == without_source_bytes.model
            and result.feature_name == without_source_bytes.feature_name
            and result.configuration_name == without_source_bytes.configuration_name
            and result.body_name is None and without_source_bytes.body_name is None,
            "archived payload or fallback body label affected the projection")
    nodes = make_nodes(result.model)
    require_closed_unattributed(nodes)
    raw = _render_local(nodes)
    decoded, _ = decode_local(raw)
    indexed = require_closed_unattributed(decoded)
    require(decoded == nodes and _render_local(decoded) == raw, "typed kernel round trip differs")
    framed = EncodePartData(raw)
    part, = DecodePartData(framed)
    require(part.data == raw and part.stored_size == len(framed), "kernel frame round trip differs")
    counts = Counter(node.kind for node in decoded)
    require((counts[VERTEX], counts[EDGE], counts[FACE]) == (8, 12, 6),
            "local body changed the recovered vertex, edge or face counts")
    expected = analytic_measures(document.brep)
    measured = boundary_measures(indexed)
    require(all(isclose(expected[name], measured[name], rel_tol=2e-12) for name in ("volume_m3", "area_m2"))
            and all(isclose(a, b, rel_tol=2e-12, abs_tol=1e-16)
                    for a, b in zip(expected["centroid_m"], measured["centroid_m"], strict=True))
            and all(isclose(a, b, rel_tol=2e-12, abs_tol=1e-16)
                    for left, right in zip(expected["bounds_m"], measured["bounds_m"], strict=True)
                    for a, b in zip(left, right, strict=True)), "kernel geometry differs from the source corners")
    return {
        "feature_name": result.feature_name,
        "configuration_name": result.configuration_name,
        "body_name": result.body_name,
        "analytical_source_si": expected,
        "decoded_kernel_si": measured,
        "raw": fingerprint(raw),
        "frame": fingerprint(framed),
        "resident_node_kinds": {SCHEMAS[kind].name: count for kind, count in sorted(counts.items())},
        "unattributed_resident_nodes": len(nodes),
        "source_payloads_removed_result_equal": True,
        "source_geometry_attributes_and_provenance_removed_result_equal": True,
        "typed_roundtrip_exact": True,
        "wrapper_roundtrip_exact": True,
        "omissions": result.omissions,
        "omitted_capabilities": result.omitted_capabilities,
        "omitted_metadata": result.omitted_metadata,
    }


def change_first(model, rows, **new_fields):
    first, *later = getattr(model, rows)
    return replace(model, **{rows: (replace(first, **new_fields), *later)})


def malformed_documents(document):
    model = document.brep
    vertex = model.vertices[0]
    edge = model.edges[0]
    points = {row.id: row.point for row in model.vertices}
    opposite = next(row.id for row in model.vertices if all(
        left != right for left, right in zip(coordinates(points[edge.start_vertex_id]), coordinates(row.point), strict=True)
    ))
    plane = model.surfaces[0]
    normal = coordinates(plane.normal)
    displacement = dict(zip(("x", "y", "z"), (a + b for a, b in zip(coordinates(plane.origin), normal, strict=True)),
                            strict=True))
    inverted = dict(zip(("x", "y", "z"), (-value for value in normal), strict=True))
    loop = model.loops[0]
    first, second, third, fourth = loop.coedge_ids
    cases = {
        "interior_vertex": change_first(model, "vertices", point=replace(vertex.point, x=vertex.point.x + 1)),
        "diagonal_edge": change_first(model, "edges", end_vertex_id=opposite),
        "line_trim_misses_vertex": change_first(model, "edges", start_parameter=edge.start_parameter + 1),
        "malformed_plane_origin": change_first(model, "surfaces", origin=replace(plane.origin, **displacement)),
        "inward_plane_normal": change_first(model, "surfaces", normal=replace(plane.normal, **inverted)),
        "scrambled_face_trim": change_first(model, "loops", coedge_ids=(first, third, second, fourth)),
        "unclosed_shell": change_first(model, "shells", closed=False),
        "reversed_face_use": change_first(model, "face_uses", reversed=True),
        "nonzero_topology_tolerance": change_first(model, "vertices", tolerance=0.01),
    }
    variants = {name: replace(document, brep=geometry) for name, geometry in cases.items()}
    feature = next(row for row in document.feature_timeline if row.kind == "imported")
    config, = document.configurations
    body, = document.bodies
    replaced_owner = {**feature.attributes, "typed_archive_owner": {
        **feature.attributes["typed_archive_owner"], "class": "moExtrusion_c",
    }}
    for name, amended in {
        "foreign_native_owner": replace(feature, attributes=replaced_owner),
        "unsupported_feature_name_override": replace(feature, name="Neutral feature name"),
    }.items():
        variants[name] = replace(
            document, feature_timeline=tuple(amended if row is feature else row for row in document.feature_timeline)
        )
    variants.update({
        "missing_brep": replace(document, brep=None),
        "inactive_configuration": replace(document, configurations=(replace(config, active=False),)),
        "unsupported_configuration_name_override": replace(document, configurations=(replace(config, name="Neutral config name"),)),
        "multiple_configurations": replace(document, configurations=(config, replace(config, id="Second", active=False))),
        "foreign_body_owner": replace(document, bodies=(replace(body, final_feature_id="Other"),)),
    })
    return variants


def must_refuse(name, document):
    try:
        project_import(document)
    except ValueError as error:
        return str(error)
    raise ValueError("invalid source unexpectedly accepted: " + name)


def verify(documents):
    variants = malformed_documents(documents["DisclosedImported"])
    variants["actual_parametric_extrude_control"] = documents["Control"]
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    enabled = True

    def guard(event, arguments):
        if enabled:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError("source projection attempted " + event)

    sys.addaudithook(guard)
    try:
        cases = {name: check_positive(document) for name, document in documents.items() if name != "Control"}
        rejected = {name: must_refuse(name, document) for name, document in variants.items()}
    finally:
        enabled = False
    require(not audit.DeniedReads, "projection attempted runtime IO")
    original, other, with_feature, with_body = (cases[key] for key in (
        "DisclosedImported", "OtherShape", "RenamedFeature", "RenamedBody",
    ))
    require(tuple(case["feature_name"] for case in cases.values())
            == ("Imported1", "Imported1", "Transfer Δ17", "Transfer Δ17")
            and all(case["configuration_name"] == "Default" and case["body_name"] is None
                    for case in cases.values()), "decoded disclosed labels differ")
    require(all(original[key] == with_feature[key] == with_body[key] and original[key] != other[key]
                for key in ("raw", "frame")), "kernel result depends on labels or ignores source geometry")
    return {
        "schema": "kit.sw2026.imported-body-source-geometry.v1",
        "disclosed_source_sha256": {name: digest for name, (_, digest) in DISCLOSED.items()},
        "construction_denied_io_events": len(audit.DeniedReads),
        "construction_source_file_reads": 0,
        "native_application_launches": 0,
        "native_solidworks_outputs": 0,
        "native_acceptance": False,
        "renamed_source_geometry_is_identical": True,
        "different_source_geometry_changes_kernel_bytes": True,
        "cases": cases,
        "refusals": rejected,
        "owning_sources_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in OWNING_SOURCES},
        "runtime": {"python": platform.python_version(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
    }


def main():
    parser = argparse.ArgumentParser(description="Verify strict disclosed SOLIDWORKS import geometry projection")
    parser.add_argument("disclosed_packet_parent", type=Path)
    arguments = parser.parse_args()
    result = verify(load_documents(arguments.disclosed_packet_parent))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=False))


if __name__ == "__main__":
    main()
