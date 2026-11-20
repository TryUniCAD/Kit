from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import fsum, hypot
from pathlib import Path, PureWindowsPath
import platform
import sys

import BuildImportedLocalPart as part_builder
from BuildLocalBodyKernel import CASES, make_nodes, prism_model
from LocalBodyKernel import _render_local, fingerprint, require
from VerifyLocalXmtWriter import compare, package_nodes
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import MakeLocalPrism
from interchange.Records.RecordProvenance import Provenance
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KAxisX, KAxisY, KAxisZ, KOriginZero, Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.EncodeData import ToData
from para.Partition import Node
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = "src/convert/adapters/solidworks/Archive/Partition/LocalPrism"
TARGET = PureWindowsPath("C:/KitPackageLocalXmt")
ADDITIONAL = {
    "SkewTriangle": (((-15.5, 3.25), (4.25, 7.5), (-1., 22.05)), (-17.25, -5.5)),
    "TranslatedPentagon": (((101.5, -58.), (121.75, -59.), (130.5, -42.),
                            (113., -29.5), (98.25, -33.)), (207., 220.5)),
}


def analytic_prism(points, levels):
    sides = tuple(zip(points, points[1:] + points[:1], strict=True))
    determinants = tuple(x1 * y2 - x2 * y1 for ((x1, y1), (x2, y2)) in sides)
    signed_area = fsum(determinants) / 2
    area = abs(signed_area)
    perimeter = fsum(hypot(x2 - x1, y2 - y1) for ((x1, y1), (x2, y2)) in sides)
    depth = levels[1] - levels[0]
    center_x = fsum((x1 + x2) * det for (((x1, _), (x2, _)), det) in zip(sides, determinants, strict=True)) / (6 * signed_area)
    center_y = fsum((y1 + y2) * det for (((_, y1), (_, y2)), det) in zip(sides, determinants, strict=True)) / (6 * signed_area)
    return area * depth, 2 * area + perimeter * depth, (center_x, center_y, fsum(levels) / 2)


def node_adapter(model):
    return tuple(Node(node.IndexValue, node.KindValue, dict(node.FieldsValue)) for node in MakeLocalPrism(model))


def complete_part(document, destination):
    blob, streams = part_builder.make_part(document, destination, "Bare", completed=True)
    part_builder.verify_part(blob, streams)
    return blob, streams


def compare_part(document, destination):
    prior_factory = part_builder.make_nodes
    require(prior_factory is make_nodes, "the comparison needs the independent research compiler as its baseline")
    prior = complete_part(document, destination)
    matches = []

    def observe_factory(model):
        matches.append(model is document.brep)
        return node_adapter(model)

    try:
        part_builder.make_nodes = observe_factory
        current = complete_part(document, destination)
    finally:
        part_builder.make_nodes = prior_factory
    require(matches == [True] and prior == current, "local compiler was bypassed or changed a complete generated part or logical stream")
    return {"part": fingerprint(current[0]), "streams": {key: fingerprint(value) for key, value in current[1].items()}}


def source_fingerprint(value):
    data = json.dumps(ToData(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(data.encode()).hexdigest()


def compare_shape(name, points, levels, expected):
    document = part_builder.make_document(name, points, levels, None)
    model = document.brep
    original = make_nodes(model)
    current = MakeLocalPrism(model)
    require(package_nodes(original) == current, "local compiler changed ordered cells or typed ownership")
    destination = str(TARGET / (name + "Bare.SLDPRT"))
    return {
        "points_mm": points, "levels_mm": levels, "neutral_brep_sha256": source_fingerprint(model),
        **compare(_render_local(original), current, expected), **compare_part(document, destination),
        "ordered_typed_nodes_exact": True, "complete_part_and_streams_exact": True,
    }


def changed(values, **fields):
    return (replace(values[0], **fields), *values[1:])


def negative_models():
    points, levels, _ = CASES["Rectangular"]
    model = prism_model("neutral-refusals", points, levels)
    sideways_points, sideways_levels = ADDITIONAL["SkewTriangle"]
    section = tuple(PlaneVector(*point) for point in sideways_points)
    profile = tuple(LineGeometry(a, b) for a, b in zip(section, section[1:] + section[:1], strict=True))
    rotated = Transform(KOriginZero, KAxisY, KAxisZ, KAxisX)
    sideways, *_ = BuildPrism("sideways-neutral", rotated, profile, *sideways_levels)
    sideways = replace(sideways, bodies=changed(sideways.bodies, design_body_id=""))
    unused = replace(model.vertices[0], id="unowned-vertex", point=SpaceVector(-2.5, 14., 3.))
    return {
        "authored_attributes": (replace(model, edges=changed(model.edges, attributes={"appearance": "blue"})), "attributes or provenance"),
        "source_provenance": (replace(model, surfaces=changed(model.surfaces, provenance=Provenance("neutral", "surface"))), "attributes or provenance"),
        "transformed_body": (replace(model, bodies=changed(model.bodies, transform=rotated)), "untransformed outward solid shell"),
        "nonzero_tolerance": (replace(model, vertices=changed(model.vertices, tolerance=0.001)), "local tolerances"),
        "bad_edge_trim": (replace(model, edges=changed(model.edges, end_parameter=3.)), "trim does not reach"),
        "invalid_plane_frame": (replace(model, surfaces=changed(model.surfaces, reference_direction=SpaceVector(0., 0., 1.))), "orthonormal frame"),
        "inward_plane": (replace(model, surfaces=changed(model.surfaces, normal=KAxisZ)), "contradicts its oriented loop"),
        "non_xy_prism": (sideways, "parallel XY section levels"),
        "unowned_vertex": (replace(model, vertices=model.vertices + (unused,)), "vertices must all belong"),
        "open_shell": (replace(model, shells=changed(model.shells, closed=False)), "untransformed outward solid shell"),
    }


def reject(name, model, reason):
    try:
        MakeLocalPrism(model)
    except ValueError as error:
        require(reason in str(error), "incorrect refusal for " + name + ": " + str(error))
        return str(error)
    raise ValueError("unadmitted neutral model reached local node construction: " + name)


def source_hashes():
    return {
        str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
        for path in sorted((
            *(ROOT / PACKAGE).glob("*.py"),
            *(Path(__file__).resolve().parent / (name + ".py") for name in (
                "BuildImportedLocalPart", "BuildLocalBodyKernel", "VerifyLocalXmtWriter",
                "VerifyLocalPrismTopology", "LocalBodyKernel",
            )),
            *(ROOT / path for path in (
                "src/convert/Geometry/Parasolid.py",
                "src/convert/adapters/solidworks/Archive/Partition/LocalWrite/EncodeLocalXmt.py",
                "re/tooling/sw2026/para/rectangle/Geometry.py",
                "re/tooling/sw2026/para/rectangle/RectanglePartition.py",
                "re/solidworks/measurements/2026/SdkLocalBodyTransmit01.json",
            )),
        ))
    }


def measure():
    sources = source_hashes()
    previous = json.loads((ROOT / "re/solidworks/measurements/2026/SdkLocalBodyTransmit01.json").read_bytes())
    for codec in ("ascii", "utf-16-le", "utf-8", "latin-1"):
        lookup(codec)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    enabled = True

    def guard(event, arguments):
        if enabled:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError("local topology construction attempted " + event)

    sys.addaudithook(guard)
    try:
        rows = {
            name: compare_shape(name, points, levels, expected)
            for name, (points, levels, expected) in (
                CASES | {name: (points, levels, analytic_prism(points, levels))
                         for name, (points, levels) in ADDITIONAL.items()}
            ).items()
        }
        refusals = {name: reject(name, model, reason) for name, (model, reason) in negative_models().items()}
    finally:
        enabled = False
    require(not audit.DeniedReads, "local topology construction attempted runtime access")
    require(len({row["raw"]["sha256"] for row in rows.values()}) == len(rows), "inputs produced duplicate kernels")
    baseline = {}
    for name in CASES:
        expected = previous["cases"][name + "Bare"]
        archive = previous["completed_part_cases"][name + "Bare"]
        raw, frame = rows[name]["raw"], rows[name]["frame"]
        require(raw == expected["raw"] and frame == expected["frame"], "earlier receipt raw/frame hashes differ")
        require(rows[name]["part"] == archive["container"] and rows[name]["streams"] == archive["streams"],
                "earlier receipt part or stream hashes differ")
        baseline[name] = {"raw_and_frame_match_previous_receipt": True,
                          "complete_part_and_stream_hashes_match_previous_receipt": True}
    return {
        "schema": "kit.sw2026.source-local-prism-topology.v1",
        "runtime": platform.python_version(),
        "cases": rows,
        "prior_receipt_comparisons": baseline,
        "neutral_refusals": refusals,
        "owning_code_and_prior_evidence_sha256": sources,
        "construction_denied_io_events": len(audit.DeniedReads),
        "input_cad_files": 0,
        "native_application_launches": 0,
        "heldout_inputs_read": 0,
        "public_import_writer_changes": 0,
    }


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2, sort_keys=True))
