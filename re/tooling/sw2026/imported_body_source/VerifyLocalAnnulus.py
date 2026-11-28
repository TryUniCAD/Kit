from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from io import BytesIO
from json import dumps, loads
from math import dist, isclose, pi, sqrt, tau
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [
    str(path)
    for path in (
        ROOT / "src",
        ROOT,
        HERE.parent,
        HERE.parent.parent,
        HERE.parent.parent / "serial",
    )
]

from BuildLocalCylinderPart import ordered_payloads, read_owners
from VerifyColdImportRoundTrip import guard, refuse
from VerifyLocalPocket import BareLabels, document, fingerprint, recipe, vector
from VerifyPlanarOpenings import baseline as old_baseline, generated as old_openings
from convert import open_document
from convert.Geometry.Parasolid import BrepTopology, DecodePartData
from convert.Geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.Geometry.Revolve.SweepVector import OffsetVector
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import (
    MakeBareImport,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeAnnularBody import (
    MakeAnnularBody,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import (
    EncodeLocalBody,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevLoops import (
    ReadRevLoops,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadLocalCyl import (
    ReadLocalCyl,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import (
    ReadLocalNodes,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.geometry.Models.VectorSpace import SpaceVector

FORMAT = "solidworks.sldprt"
NATIVE_BUILD = "34.5.2.0604"
CORPUS = ROOT / "re/solidworks/v2026/corpus/curves-discovery"
MANIFEST_SHA = "83fdec0c415f6b2152d8df6bb12deba1b24313e8580597452505b139ec59a42e"
D19_SHA = "2a9846fa9ddc882ef3b848dfc311a7859d102ab9fa7687769cdba88a7b510439"
SCHEMA = b"SCH_3701250_37102_13006"
PASSAGE_RECEIPT = ROOT / "re/solidworks/measurements/2026/PlanarThroughOpening01.json"
PASSAGE_SHA = "0bb97a7f13662c26ee4f5c2029cd80e8bceb9f127342bda0a961d93784f3ff52"
CASES = {
    "AxisRing": (
        5.0,
        11.0,
        16.0,
        (1.0, 2.0, -3.0),
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
        False,
    ),
    "ObliqueRing": (
        2.75,
        8.625,
        11.25,
        (4.125, -11.25, 19.5),
        (-0.6, 0.8, 0.0),
        (0.0, 0.0, 1.0),
        True,
    ),
}


def oriented(sign):
    assert sign in ("+", "-")
    return 1 if sign == "+" else -1


def wire_rings(nodes, body):
    rows = {}
    owners = {}
    for face_id in ReadBodyFaces(nodes, body, 4):
        face = nodes[face_id]
        carrier = nodes[face.Integer("surface")]
        loops, fins = ReadRevLoops(nodes, face, True)
        assert carrier.Integer("owner") == face_id and carrier.KindValue in (50, 51)
        assert len(loops) == len(fins) == 2
        face_sign, surface_sign = face.String("sense"), carrier.String("sense")
        raw_frame = carrier.FieldsValue["normal" if carrier.KindValue == 50 else "axis"]
        rows[face_id] = {
            "loops": loops,
            "fins": fins,
            "carrier_kind": carrier.KindValue,
            "carrier": carrier.IndexValue,
            "face_sense": face_sign,
            "carrier_sense": surface_sign,
            "origin_m": carrier.FieldsValue["pvec"],
            "raw_axis": raw_frame,
            "effective_sign": oriented(face_sign) * oriented(surface_sign),
        }
        for fin_id in fins:
            assert fin_id not in owners
            owners[fin_id] = face_id
        if carrier.KindValue == 51:
            rows[face_id]["radius_m"] = carrier.FieldsValue["radius"]
    assert len(owners) == 8
    walls = sorted(
        (row for row in rows.values() if row["carrier_kind"] == 51),
        key=lambda row: row["radius_m"],
    )
    assert len(walls) == 2 and [row["effective_sign"] for row in walls] == [-1, 1]
    edge_ids = WalkXmtChain(
        nodes, body.Integer("edge"), 16, OwnerField="owner", OwnerValue=body.IndexValue
    )
    edges = {}
    face_pairs = set()
    accounted_fins = set()
    for edge_id in edge_ids:
        edge = nodes[edge_id]
        fin = nodes[edge.Integer("halfedge")]
        mate = nodes[fin.Integer("other")]
        circle = nodes[edge.Integer("curve")]
        assert (fin.String("sense"), mate.String("sense")) == ("+", "-")
        assert fin.Integer("edge") == mate.Integer("edge") == edge_id
        assert circle.KindValue == 31 and circle.Integer("owner") == edge_id
        head_face, mate_face = (owners[value.IndexValue] for value in (fin, mate))
        cap_id, wall_id = sorted(
            (head_face, mate_face), key=lambda value: rows[value]["carrier_kind"]
        )
        cap, wall = rows[cap_id], rows[wall_id]
        assert (cap["carrier_kind"], wall["carrier_kind"]) == (50, 51)
        assert circle.FieldsValue["centre"] == cap["origin_m"]
        assert circle.FieldsValue["radius"] == wall["radius_m"]
        assert not accounted_fins.intersection((fin.IndexValue, mate.IndexValue))
        accounted_fins.update((fin.IndexValue, mate.IndexValue))
        face_pairs.add((cap_id, wall_id))
        edges[edge_id] = {
            "positive_fin": fin.IndexValue,
            "negative_fin": mate.IndexValue,
            "positive_owner": head_face,
            "negative_owner": mate_face,
            "cap": cap_id,
            "wall": wall_id,
            "circle": circle.IndexValue,
            "radius_m": circle.FieldsValue["radius"],
        }
    assert len(face_pairs) == len(edges) == 4 and accounted_fins == set(owners)
    assert not any(node.KindValue in (18, 29) for node in nodes.values())
    return {"body": body.IndexValue, "faces": rows, "edges": edges}


def native():
    catalog = (CORPUS / "Manifest.json").read_bytes()
    assert fingerprint(catalog)["sha256"] == MANIFEST_SHA
    manifest = loads(catalog)
    (case,) = (row for row in manifest["records"] if row["file"] == "D19Annulus.SLDPRT")
    assert manifest["native_build"] == NATIVE_BUILD and case["split"] == "discovery"
    data = (CORPUS / case["file"]).read_bytes()
    assert fingerprint(data)["sha256"] == case["sha256"] == D19_SHA
    archive = SldprtArchive.from_bytes(data)
    partition = archive.require(KPartitionStream)
    (row,) = (value for value in case["streams"] if value["name"] == KPartitionStream)
    assert fingerprint(partition)["sha256"] == row["sha256"]
    active, deltas = DecodePartData(partition, KPartitionStream)
    assert (active.kind, deltas.kind) == (
        "partition",
        "deltas",
    ) and SCHEMA in active.data
    assert (
        fingerprint(active.data)["sha256"]
        == "1b04be9c2b3c1b8bb4ed50a8b7752e6e889c0145218d2ab977102d14d7449783"
    )
    assert (
        fingerprint(deltas.data)["sha256"]
        == "35868a2d97dfc45a1a1d59e88373e9967a683b88dc374478fda4c6c8a0763bd2"
    )
    graph = ReadActiveNodes(active.data)
    kinds = Counter(node.KindValue for node in graph.values())
    assert {
        kind: kinds[kind] for kind in (12, 13, 14, 15, 16, 17, 18, 19, 29, 31, 50, 51)
    } == {
        12: 1,
        13: 2,
        14: 4,
        15: 8,
        16: 4,
        17: 8,
        18: 0,
        19: 2,
        29: 0,
        31: 4,
        50: 2,
        51: 2,
    }
    (body,) = (node for node in graph.values() if node.KindValue == 12)
    values = wire_rings(graph, body)
    assert values["faces"][39]["loops"] == (50, 58)
    assert values["faces"][64]["loops"] == (70, 76)
    assert {
        row["carrier_sense"]
        for row in values["faces"].values()
        if row["carrier_kind"] == 51
    } == {"-"}
    return {
        "native_build": NATIVE_BUILD,
        "catalog": fingerprint(catalog),
        "saved_part": fingerprint(data),
        "wire_schema": SCHEMA.decode(),
        "active": fingerprint(active.data),
        "deltas": fingerprint(deltas.data),
        "partition": fingerprint(partition),
        "kind_inventory": dict(kinds),
        "ownership": values,
    }


def geometry(name, specification):
    inner, outer, height, start, axis, radial, hole_first = specification
    section = ((inner, 0.0), (outer, 0.0), (outer, height), (inner, height))
    shape = BuildFullSweep(
        name, section, SpaceVector(*start), SpaceVector(*axis), SpaceVector(*radial)
    )
    caps = {row.id for row in shape.surfaces if isinstance(row, PlaneSurface)}
    return replace(
        shape,
        bodies=(replace(shape.bodies[0], design_body_id=""),),
        faces=tuple(
            (
                replace(face, loop_ids=face.loop_ids[::-1])
                if hole_first and face.surface_id in caps
                else face
            )
            for face in shape.faces
        ),
    )


def mesh_metrics(radius_set, centres, axis):
    inner, outer = radius_set
    first, last = centres
    height = dist(first, last)
    section_area = pi * (outer**2 - inner**2)
    centroid = tuple((a + b) / 2 for a, b in zip(first, last, strict=True))
    radial_extent = tuple(outer * sqrt(max(0.0, 1 - value**2)) for value in axis)
    low = tuple(
        min(a, b) - extent
        for a, b, extent in zip(first, last, radial_extent, strict=True)
    )
    high = tuple(
        max(a, b) + extent
        for a, b, extent in zip(first, last, radial_extent, strict=True)
    )
    return {
        "volume_mm3": section_area * height,
        "area_mm2": 2 * section_area + tau * (outer + inner) * height,
        "centroid_mm": centroid,
        "bounds_mm": (low, high),
        "radii_mm": radius_set,
        "height_mm": height,
    }


def close(observed, expected):
    if isinstance(observed, (list, tuple)):
        assert isinstance(expected, (list, tuple))
        for a, b in zip(observed, expected, strict=True):
            close(a, b)
    else:
        assert isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-12), (
            observed,
            expected,
        )


def measure_shape(shape, specification):
    inner, outer, height, start, axis, radial, hole_first = specification
    topo = BrepTopology(shape)
    caps = tuple(
        face
        for face in shape.faces
        if isinstance(topo.surface_by_id[face.surface_id], PlaneSurface)
    )
    walls = sorted(
        (
            face
            for face in shape.faces
            if isinstance(topo.surface_by_id[face.surface_id], CylinderSurface)
        ),
        key=lambda face: topo.surface_by_id[face.surface_id].radius,
    )
    assert len(caps) == len(walls) == 2 and [face.same_sense for face in walls] == [
        False,
        True,
    ]
    rings = {row.id: row for row in shape.curves}
    assert len(rings) == 4
    expected_end = tuple(
        value + height * signed for value, signed in zip(start, axis, strict=True)
    )
    expected_roles = (False, True) if hole_first else (True, False)
    measured_axis = vector(topo.surface_by_id[walls[1].surface_id].axis)
    close(measured_axis, axis)
    measured_centres = []
    for face in caps:
        plane = topo.surface_by_id[face.surface_id]
        centre = vector(plane.origin)
        measured_centres.append(centre)
        assert tuple(topo.loops[key].outer for key in face.loop_ids) == expected_roles
        normal = tuple(
            value if face.same_sense else -value for value in vector(plane.normal)
        )
        close(
            normal,
            (
                axis
                if dist(centre, expected_end) < 1e-12
                else tuple(-value for value in axis)
            ),
        )
        for key in face.loop_ids:
            loop = topo.loops[key]
            (use,) = loop.coedge_ids
            edge = topo.edges[topo.coedges[use].edge_id]
            circle = rings[edge.curve_id]
            assert isinstance(circle, CircleCurve) and circle.center == plane.origin
            assert edge.start_vertex_id == edge.end_vertex_id and (
                edge.start_parameter,
                edge.end_parameter,
            ) == (0.0, tau)
            close(
                vector(topo.vertex_by_id[edge.start_vertex_id].point),
                vector(
                    OffsetVector(
                        circle.center, circle.reference_direction, circle.radius
                    )
                ),
            )
            close(circle.radius, outer if loop.outer else inner)
            close(vector(circle.axis), axis)
            close(vector(circle.reference_direction), radial)
    measured_centres.sort(key=lambda point: dist(point, start))
    close(measured_centres, (start, expected_end))
    recovered = tuple(topo.surface_by_id[face.surface_id].radius for face in walls)
    expected_area = 2 * pi * (outer**2 - inner**2 + (outer + inner) * height)
    expected_volume = pi * (outer - inner) * (outer + inner) * height
    result = mesh_metrics(recovered, measured_centres, measured_axis)
    close(
        (
            result["volume_mm3"],
            result["area_mm2"],
            result["centroid_mm"],
            result["radii_mm"],
            result["height_mm"],
        ),
        (
            expected_volume,
            expected_area,
            tuple(a + 0.5 * height * b for a, b in zip(start, axis, strict=True)),
            (inner, outer),
            height,
        ),
    )
    direction_y = (
        axis[1] * radial[2] - axis[2] * radial[1],
        axis[2] * radial[0] - axis[0] * radial[2],
        axis[0] * radial[1] - axis[1] * radial[0],
    )
    expected_bounds = tuple(
        tuple(
            (
                min(a, b) - outer * sqrt(x * x + y * y)
                if sign < 0
                else max(a, b) + outer * sqrt(x * x + y * y)
            )
            for a, b, x, y in zip(start, expected_end, radial, direction_y, strict=True)
        )
        for sign in (-1, 1)
    )
    close(result["bounds_mm"], expected_bounds)
    return result | {
        "cap_roles": expected_roles,
        "portable_derived_seams": len(shape.vertices),
    }


def read_modes(blob, owner, specification):
    readings = []
    reports = {}
    for mode, full in (("full", True), ("design", False)):
        current = open_document(
            BytesIO(blob),
            source_format=FORMAT,
            strict=True,
            include_brep=full,
            include_tessellation=False,
            configuration=None if full else "Default",
        )
        (body,) = current.bodies
        (feature,) = (
            step
            for step in current.feature_timeline
            if step.kind is FeatureKind.IMPORTED
        )
        assert body.name == feature.name == owner["local_group"]
        assert (
            body.final_feature_id
            == feature.id
            == f"sldprt:feature:{owner['feature_id']}"
        )
        assert body.attributes["native_object_id"] == owner["feature_id"]
        top = body.topology
        counts = (
            top.solid_count,
            top.shell_count,
            top.face_count,
            top.edge_count,
            top.vertex_count,
        )
        assert counts == (1, 1, 4, 4, 4)
        neutral = current.to_json(indent=None)
        restored = CadDocument.from_json(neutral)
        assert neutral == restored.to_json(indent=None)
        report = {
            "feature": feature.id,
            "topology": counts,
            "json": fingerprint(neutral.encode()),
        }
        if full:
            assert current.brep is not None and len(current.brep_payloads) == 3
            assert current.brep.bodies[0].design_body_id == body.id
            assert not current.brep.validate(frozenset((body.id,)))
            report["geometry"] = measure_shape(current.brep, specification)
        else:
            assert current.brep is None and not current.brep_payloads
        readings.append(current)
        reports[mode] = report
    full, design = readings
    assert (
        full.feature_timeline == design.feature_timeline
        and full.configurations == design.configurations
    )
    assert full.bodies[0].provenance == design.bodies[0].provenance
    return readings, reports


def reject(call, explanation):
    try:
        call()
    except ValueError as error:
        assert explanation in str(error), (explanation, str(error))
        return str(error)
    raise AssertionError("unsupported annulus boundary entered the codec")


def guards(name, shape, nodes, offsets, options, labels):
    (bore,) = (
        value
        for value in shape.surfaces
        if isinstance(value, CylinderSurface) and value.radius == CASES[name][0]
    )
    inside = next(face for face in shape.faces if face.surface_id == bore.id)
    other = next(
        value
        for value in shape.surfaces
        if isinstance(value, CylinderSurface) and value.id != bore.id
    )
    shifted = replace(
        bore, origin=OffsetVector(bore.origin, bore.reference_direction, 1.0)
    )
    equal = replace(bore, radius=other.radius)

    def with_carrier(surface):
        return replace(
            shape,
            surfaces=tuple(
                surface if item.id == bore.id else item for item in shape.surfaces
            ),
        )

    edge, *edges = shape.edges
    wire_carrier = next(value for value in nodes.values() if value.KindValue == 51)
    wire_face = nodes[wire_carrier.Integer("owner")]
    swapped = replace(
        wire_carrier,
        FieldsValue=dict(wire_carrier.FieldsValue) | {"owner": nodes[1].IndexValue},
    )
    wrong_sign = replace(
        wire_face,
        FieldsValue=dict(wire_face.FieldsValue)
        | {"sense": "-" if wire_face.String("sense") == "+" else "+"},
    )
    owned = next(value for value in nodes.values() if value.KindValue == 16)
    alternate_fin = nodes[owned.Integer("halfedge")].Integer("other")
    inverted = replace(
        owned, FieldsValue=dict(owned.FieldsValue) | {"halfedge": alternate_fin}
    )
    wire_cases = {
        "foreign_carrier_owner": (swapped, "foreign cap or wall ownership"),
        "reversed_wall_face": (wrong_sign, "opposing wall sense"),
        "negative_primary_fin": (
            inverted,
            "foreign edge or circular carrier ownership",
        ),
    }
    result = {}
    for key, (row, message) in wire_cases.items():
        contrast = nodes | {row.IndexValue: row}
        result[key + "_read"] = reject(lambda: ReadLocalCyl(contrast, offsets), message)
        result[key + "_write"] = reject(
            lambda: EncodeLocalBody(labels.FeatureName, tuple(contrast.values())),
            message,
        )
    cases = {
        "noncoaxial": (with_carrier(shifted), "distinct coaxial"),
        "equal_radii": (with_carrier(equal), "distinct coaxial"),
        "partial_rim": (
            replace(shape, edges=(replace(edge, end_parameter=pi), *edges)),
            "one full circle trim",
        ),
        "outward_bore": (
            replace(
                shape,
                faces=tuple(
                    replace(value, same_sense=True) if value.id == inside.id else value
                    for value in shape.faces
                ),
            ),
            "opposing wall sense",
        ),
    }
    for role, (boundary, why) in cases.items():
        result[role] = reject(
            lambda: MakeBareImport(document(boundary), options, labels), why
        )
    return result


def model_case(name, specification):
    shape = geometry(name, specification)
    assert not shape.validate()
    requested = document(shape)
    labels = BareLabels(name, "Default", "Imported annulus")
    locator = PureWindowsPath(r"C:\KitAnnularImport\Candidates") / (name + ".SLDPRT")
    options = recipe(labels, locator, 1790000000)
    candidate = MakeBareImport(requested, options, labels)
    repeat = MakeBareImport(document(geometry(name, specification)), options, labels)
    assert (
        candidate.BytesValue == repeat.BytesValue
        and candidate.StreamsValue == repeat.StreamsValue
    )
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    assert len(archive.streams) == 12 and archive.streams == candidate.StreamsValue
    _, local, group, mark = ordered_payloads(candidate.BytesValue, archive)
    owner = read_owners(archive, group, mark)
    nodes, offsets = ReadLocalNodes(local, AllowPeriodic=True)
    assert len(nodes) == 37 and tuple(nodes.values()) == MakeAnnularBody(shape)
    assert EncodeLocalBody(group, tuple(nodes.values())) == archive.require(
        KLocalBodyStream
    )
    topology = wire_rings(nodes, nodes[1])
    readings, report = read_modes(candidate.BytesValue, owner, specification)
    for route in ("registry", "writer", "adapter"):
        for model in (requested, *readings):
            refuse(route, model, {})
    return {
        "candidate": fingerprint(candidate.BytesValue),
        "local_kernel": fingerprint(local),
        "streams": {key: fingerprint(value) for key, value in archive.streams.items()},
        "wire": topology,
        "typed_local_cells": len(nodes),
        "archive_owners": owner,
        "locator": str(locator),
        "written_at": 1790000000,
        "portable_source_geometry": measure_shape(shape, specification),
        "sdk": report,
        "guard_refusals": guards(name, shape, nodes, offsets, options, labels),
        "public_write_refusals": 9,
        "authored_parametric_history": False,
    }


def generate():
    with guard() as events:
        results = {
            name: model_case(name, specification)
            for name, specification in CASES.items()
        }
    assert len({row["candidate"]["sha256"] for row in results.values()}) == len(results)
    return {"cases": results, "runtime_input_reads": len(events)}


def baseline():
    baseline_result = old_baseline()
    data = PASSAGE_RECEIPT.read_bytes()
    assert fingerprint(data)["sha256"] == PASSAGE_SHA
    assert loads(dumps(old_openings())) == loads(data)["generate"]
    return baseline_result | {
        "exact_planar_through_cases": 2,
        "exact_through_receipt": fingerprint(data),
        "logical_stream_hashes": 96,
    }


def main():
    methods = {
        "native-observation": native,
        "model-generate": generate,
        "baseline": baseline,
    }
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("all", *methods))
    args = parser.parse_args()
    if args.mode == "all":
        result = {
            mode: loads(
                check_output((sys.executable, "-I", "-B", str(HERE), mode), timeout=60)
            )
            for mode in methods
        }
        result |= {
            "schema": "kit.sw2026.annular-local-import.v1",
            "tool": fingerprint(HERE.read_bytes()),
            "runtime": sys.version.split()[0],
            "compressor": ZLIB_RUNTIME_VERSION,
            "native_processes_started": 0,
            "new_heldout_cases": 0,
            "new_public_writer_admission": False,
        }
    else:
        result = methods[args.mode]()
    print(dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
