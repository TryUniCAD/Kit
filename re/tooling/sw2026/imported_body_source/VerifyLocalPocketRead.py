from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyLocalPocket import (
    POCKETS, ROOT, BareLabels, CadDocument, MakeBareImport, controls, counts,
    document, fingerprint, guard, measures, native, pocket, prepare, read_back,
    recipe, refuse, rejected,
)
from LocalBodyEnvelope import LocalBody, encode
from LocalBodyKernel import _render_local
from para.Partition import Node
from convert import open_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.api.ApiContext import KConvertEngine
from interchange.Enums.EnumFeatures import FeatureKind

CONSTRUCTION = ROOT / "re/solidworks/measurements/2026/LocalPocketTopology01.json"
CONSTRUCTION_SHA = "8d847b127137b6efdab54cea127af0ce083066f76e027cc64cbcf9c6dd05afb6"
FORMAT = "solidworks.sldprt"


def open_part(data, include_brep, configuration=None):
    return open_document(BytesIO(data), source_format=FORMAT, strict=True,
                         include_brep=include_brep, include_tessellation=False,
                         configuration=configuration)


def verify_projection(data, include_brep, sections, owners, configuration=None):
    result = open_part(data, include_brep, configuration)
    neutral = result.to_json(indent=None)
    clone = CadDocument.from_json(neutral)
    assert clone.to_json(indent=None) == neutral
    assert len(clone.bodies) == len(result.bodies) == 1
    body, = result.bodies
    imported, = (step for step in result.feature_timeline if step.kind is FeatureKind.IMPORTED)
    assert body.name == imported.name == owners["local_group"]
    assert imported.id == body.final_feature_id == f"sldprt:feature:{owners['feature_id']}"
    assert body.attributes["native_object_id"] == owners["feature_id"]
    topology = body.topology
    assert (topology.solid_count, topology.shell_count, topology.face_count,
            topology.edge_count, topology.vertex_count) == (1, 1, 11, 24, 16)
    assert clone.feature_timeline == result.feature_timeline and clone.bodies == result.bodies
    assert clone.configurations == result.configurations and clone.source.sha256 == sha256(data).hexdigest()
    assert not any(diag.code == "sldprt.local_geometry_rejected" for diag in result.diagnostics)
    if include_brep:
        assert result.brep is not None and clone.brep == result.brep
        assert counts(result.brep) == (11, 12, 24, 48, 16)
        assert result.brep.bodies[0].design_body_id == body.id
        assert not result.brep.validate(frozenset((body.id,)))
        assert len(result.brep_payloads) == len(clone.brep_payloads) == 3
        geometry = measures(result.brep, sections)
    else:
        assert result.brep is clone.brep is None and not result.brep_payloads and not clone.brep_payloads
        geometry = None
    return result, {"feature_id": body.final_feature_id, "native_object_id": body.attributes["native_object_id"],
                    "label": body.name, "topology": [topology.solid_count, topology.shell_count,
                                                       topology.face_count, topology.edge_count, topology.vertex_count],
                    "geometry": geometry, "neutral_json": True,
                    "native_payloads": len(result.brep_payloads),
                    "configuration_id": result.configurations[0].id,
                    "json_sha256": sha256(neutral.encode()).hexdigest()}


def generated_nodes(geometry):
    from VerifyLocalPocket import MakeLocalPocket
    return {node.IndexValue: node for node in MakeLocalPocket(geometry)}


def altered_nodes(cells, node, **values):
    return tuple(replace(row, FieldsValue=dict(row.FieldsValue) | values) if row is node else row
                 for row in cells.values())


def changed_part(result, stream, data):
    return BuildSldprt(dict(result.StreamsValue) | {stream: data}, FormatVersion=4)


def activity_contrasts(result, model, group, rim):
    cells = generated_nodes(model)
    face = cells[rim["face"]]
    plane = cells[face.Integer("surface")]
    inner = cells[rim["loop_ids"][1]]
    other = next(node.IndexValue for node in cells.values() if node.KindValue == 14 and node is not face)
    vertex = next(node for node in cells.values() if node.KindValue == 18)
    first_fin = cells[vertex.Integer("halfedge")]
    raw = _render_local(tuple(Node(row.IndexValue, row.KindValue, dict(row.FieldsValue)) for row in
                              altered_nodes(cells, inner, face=other)))
    point = plane.FieldsValue["pvec"]
    offset_plane = altered_nodes(cells, plane, pvec=(*point[:2], point[2] + 0.000125))

    cases = {
        "foreign_group": (KLocalBodyStream, EncodeLocalBody("Foreign pocket", tuple(cells.values()), AllowPocket=True), "storage key differs"),
        "foreign_rim_face": (KLocalBodyStream, encode(LocalBody(group, raw)), "owner chain is not reciprocal"),
        "missing_fin_rotation": (KLocalBodyStream, EncodeLocalBody(group, altered_nodes(cells, first_fin, next_at_vx=0), AllowPocket=True), "vertex has inconsistent fin rotation"),
        "false_carrier_station": (KLocalBodyStream, EncodeLocalBody(group, offset_plane, AllowPocket=True), "trim leaves its supporting plane"),
        "competing_payload": ("Contents/OtherLocalBody", result.StreamsValue[KLocalBodyStream], "sole selected payload group"),
    }
    return {
        role: {
            mode: rejected(lambda: open_part(changed_part(result, stream, data), full), reason)
            for mode, full in (("full", True), ("design", False))
        }
        for role, (stream, data, reason) in cases.items()
    }


def reversed_carrier(result, model, group, rim, sections, owners):
    cells = generated_nodes(model)
    face = cells[rim["face"]]
    plane = cells[face.Integer("surface")]
    cells[face.IndexValue] = replace(face, FieldsValue=dict(face.FieldsValue) | {"sense": "-"})
    normal = tuple(-value for value in plane.FieldsValue["normal"])
    stored = EncodeLocalBody(group, altered_nodes(cells, plane, normal=normal), AllowPocket=True)
    data = changed_part(result, KLocalBodyStream, stored)
    full, report = verify_projection(data, True, sections, owners)
    planes = {value.id: value for value in full.brep.surfaces}
    cap, = (value for value in full.brep.faces if len(value.loop_ids) == 2)
    assert not cap.same_sense and planes[cap.surface_id].normal.z == -1
    return {"full": report, "alternate_carrier_preserved": True}


def check_generated(name, sections, baseline):
    geometry = pocket(name, sections)
    neutral = document(geometry)
    labels = BareLabels(name, "Default", baseline["archive_owners"]["local_group"])
    target = PureWindowsPath(baseline["logical_destination"])
    result = MakeBareImport(neutral, recipe(labels, target, baseline["written_at"]), labels)
    data = result.BytesValue
    assert fingerprint(data) == baseline["part"]
    assert {key: fingerprint(value) for key, value in result.StreamsValue.items()} == baseline["streams"]
    _, typed_brep, owners, rim = read_back(result, geometry)
    full, normal = verify_projection(data, True, sections, owners)
    design, partial = verify_projection(data, False, sections, owners, "Default")
    assert full.feature_timeline == design.feature_timeline and full.configurations == design.configurations
    assert full.bodies[0].provenance == design.bodies[0].provenance
    assert typed_brep == replace(full.brep, bodies=(replace(full.brep.bodies[0], design_body_id=""),))
    assert normal["topology"] == partial["topology"]
    raw = KConvertEngine.read(data, format_id=FORMAT, options=ReadOptions(
        strict=True, include_brep=True, include_tessellation=False, extract_raw_brep=True,
    ))
    assert raw.brep is None and len(raw.brep_payloads) == 3
    assert raw.feature_timeline == full.feature_timeline
    for route in ("registry", "writer", "adapter"):
        for value in (neutral, full, design):
            refuse(route, value, {})
    return {"archive": fingerprint(data), "stream_digests": "exact", "full": normal, "design": partial,
            "raw_payloads": len(raw.brep_payloads), "unmeasured_publication_refusals": 9,
            "refusals": activity_contrasts(result, geometry, labels.FeatureName, rim),
            "equivalent_reversed_plane": reversed_carrier(result, geometry, labels.FeatureName, rim, sections, owners)}


def generated():
    previous = CONSTRUCTION.read_bytes()
    assert sha256(previous).hexdigest() == CONSTRUCTION_SHA
    prior = loads(previous)["generate"]["cases"]
    prepare()
    with guard() as events:
        rows = {name: check_generated(name, sections, prior[name]) for name, sections in POCKETS.items()}
    return {"frozen_construction": fingerprint(previous), "cases": rows, "runtime_input_reads": len(events)}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("all", "generated", "native", "controls"))
    parser.add_argument("--disclosed-native-directory", type=Path)
    args = parser.parse_args()
    if args.mode in ("all", "native") and args.disclosed_native_directory is None:
        parser.error("the pinned disclosed directory is required for native observations")
    modes = {"generated": generated, "native": lambda: native(args.disclosed_native_directory), "controls": controls}
    if args.mode == "all":
        output = {name: loads(check_output((sys.executable, "-I", "-B", str(HERE), name,
                                           "--disclosed-native-directory", str(args.disclosed_native_directory)), timeout=60))
                  for name in modes}
        output |= {"schema": "kit.sw2026.strict-local-pocket-read.v1", "probe_sha256": fingerprint(HERE.read_bytes())["sha256"],
                   "native_processes_started": 0, "new_heldout_cases": 0, "new_public_writer_admission": False}
    else:
        output = modes[args.mode]()
    print(dumps(output, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
