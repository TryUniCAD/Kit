from codecs import lookup
from dataclasses import replace
from importlib import import_module
import json
from math import isclose, sqrt, tau
from pathlib import Path, PureWindowsPath

from BuildImportedLocalPart import AUTHORED_AMBIENT, DEFAULT_FEATURE_NAME, EPOCH
from BuildLocalCylinder import (
    CASES,
    CylinderInput,
    expected_measures,
    make_neutral,
    measure_neutral,
    read_typed,
    verify_graph,
    write_typed,
)
from BuildLocalCylinderPart import (
    make_part as research_part,
    ordered_payloads,
    read_owners,
)
from VerifyBareImportPackage import (
    BareLabels,
    ambient_input,
    fingerprint,
    guard_build,
    recipe,
    require,
)
from convert import open_document
from convert.Geometry.Parasolid import ConicPoint, DecodeBrepModel
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import (
    MakeBareImport,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability, Severity
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource

ROOT = Path(__file__).resolve().parents[4]
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
ARCHIVE = ROOT / "src/convert/adapters/solidworks/Archive"
NATIVE_PATH = PureWindowsPath(r"C:\KitCylinderPart01\Candidates")
OBLIQUE = CylinderInput(
    (-7.125, 13.375, 24.625),
    (2 / 3, -1 / 3, 2 / 3),
    (1 / sqrt(5), 2 / sqrt(5), 0.0),
    5.9375,
    32.5,
)
LOCK = "SealedPeriodicImportedSourceLock01.json"
LIFECYCLE = "GeneratedLocalCylinderPartNative01.json"
PLANAR_REFERENCE = "SdkBareCylinderGeometry01.json"


def vector(value):
    return (value.x, value.y, value.z)


def negate(value):
    return SpaceVector(*(-component for component in vector(value)))


def author_boundary(model):
    centre, axis, radial = (
        SpaceVector(*value) for value in (model.start_mm, model.axis, model.radial)
    )
    radius = model.radius_mm
    far = OffsetVector(centre, axis, model.height_mm)
    side = CylinderSurface("measurement-wall", centre, axis, radial, radius)
    faces, surfaces, loops, coedges, edges, curves, vertices = (
        [],
        [side],
        [],
        [],
        [],
        [],
        [],
    )
    for name, point, normal, reference in (
        ("far", far, axis, radial),
        ("near", centre, negate(axis), negate(radial)),
    ):
        rim = CircleCurve(
            f"{name}:orbit", point, negate(normal), negate(reference), radius
        )
        cap = PlaneSurface(f"{name}:plane", point, normal, reference)
        seam = BrepVertex(
            f"{name}:period", OffsetVector(rim.center, rim.reference_direction, radius)
        )
        edge = BrepEdge(f"{name}:boundary", seam.id, seam.id, rim.id, 0.0, tau)
        cap_use = BrepCoedge(f"{name}:cap-use", edge.id, reversed=True)
        side_use = BrepCoedge(f"{name}:side-use", edge.id)
        cap_loop = BrepLoop(f"{name}:cap-loop", (cap_use.id,), outer=True)
        side_loop = BrepLoop(f"{name}:side-loop", (side_use.id,), outer=name == "far")
        faces.append(BrepFace(f"{name}:cap", cap.id, (cap_loop.id,)))
        surfaces.append(cap)
        loops.extend((cap_loop, side_loop))
        coedges.extend((cap_use, side_use))
        edges.append(edge)
        curves.append(rim)
        vertices.append(seam)
    faces.append(BrepFace("mantle", side.id, ("far:side-loop", "near:side-loop")))
    face_uses = tuple(BrepFaceUse(face.id + ":owner", face.id) for face in faces)
    shell = BrepShell("parent-shell", tuple(use.id for use in face_uses), closed=True)
    shell_use = BrepShellUse("connected-outward-shell", shell.id)
    region = BrepRegion("closed-region", (shell_use.id,), solid=True)
    return BrepModel(
        curves=tuple(curves),
        surfaces=tuple(surfaces),
        vertices=tuple(vertices),
        edges=tuple(edges),
        coedges=tuple(coedges),
        loops=tuple(loops),
        faces=tuple(faces),
        face_uses=face_uses,
        shells=(shell,),
        shell_uses=(shell_use,),
        regions=(region,),
        bodies=(BrepBody("portable-solid", (region.id,)),),
    )


def neutral_document(boundary):
    return CadDocument(
        CadSource("kit.neutral", "", ""),
        (Configuration("selected", "Default", True),),
        (),
        (),
        (),
        (),
        (),
        (),
        brep=boundary,
        capabilities=frozenset({Capability.KBrep, Capability.KConfigurations}),
    )


def construct(document, name):
    destination = NATIVE_PATH / (name + ".SLDPRT")
    labels = BareLabels(name, document.configurations[0].name, DEFAULT_FEATURE_NAME)
    settings = recipe(labels, destination, EPOCH)
    ambient = ambient_input(AUTHORED_AMBIENT, EPOCH)
    require(
        not SldprtWriter().supports(document, str(destination)),
        "public writer admitted the experimental profile",
    )
    return MakeBareImport(document, settings, labels, AmbientValue=ambient)


def compare_measures(actual, expected, label):
    for name in ("volume_mm3", "area_mm2"):
        require(
            isclose(actual[name], expected[name], rel_tol=2e-7),
            f"{label} {name} differs",
        )
    for value, target in zip(
        (*actual["centroid_mm"], *actual["bounds_mm"][0], *actual["bounds_mm"][1]),
        (
            *expected["centroid_mm"],
            *expected["bounds_mm"][0],
            *expected["bounds_mm"][1],
        ),
        strict=True,
    ):
        require(
            isclose(value, target, rel_tol=0.0, abs_tol=1e-7),
            f"{label} centroid or bounds differs",
        )


def compare_seams(source, restored):
    (side,) = (
        surface for surface in source.surfaces if type(surface) is CylinderSurface
    )
    source_rims = sorted(
        source.curves, key=lambda curve: DotVector(curve.center, side.axis)
    )
    restored_rims = sorted(
        restored.curves, key=lambda curve: DotVector(curve.center, side.axis)
    )
    source_edges = {edge.curve_id: edge for edge in source.edges}
    restored_edges = {edge.curve_id: edge for edge in restored.edges}
    source_points = {vertex.id: vertex.point for vertex in source.vertices}
    restored_points = {vertex.id: vertex.point for vertex in restored.vertices}
    for expected, actual in zip(source_rims, restored_rims, strict=True):
        expected_point = source_points[source_edges[expected.id].start_vertex_id]
        edge = restored_edges[actual.id]
        actual_point = restored_points[edge.start_vertex_id]
        require(
            edge.start_vertex_id == edge.end_vertex_id
            and (edge.start_parameter, edge.end_parameter) == (0.0, tau)
            and vector(actual_point) == vector(ConicPoint(actual, 0.0))
            and all(
                isclose(left, right, abs_tol=1e-12, rel_tol=0.0)
                for left, right in zip(
                    (
                        *vector(actual.center),
                        *vector(actual.axis),
                        *vector(actual.reference_direction),
                        actual.radius,
                        *vector(actual_point),
                    ),
                    (
                        *vector(expected.center),
                        *vector(expected.axis),
                        *vector(expected.reference_direction),
                        expected.radius,
                        *vector(expected_point),
                    ),
                    strict=True,
                )
            ),
            "reconstructed circle changed its source orientation or seam",
        )


def verify_part(part, source, expected):
    archive = SldprtArchive.from_bytes(part.BytesValue)
    require(
        archive.streams == part.StreamsValue and len(archive.streams) == 12,
        "ordinary archive stream ownership changed",
    )
    intake, kernel, group, mark = ordered_payloads(part.BytesValue, archive)
    owner = read_owners(archive, group, mark)
    require(
        owner["atom_id"] == part.AtomId
        and owner["feature_id"] == NativeNodeId(part.FeatureValue)
        and owner["local_group"] == DEFAULT_FEATURE_NAME
        and owner["configured_body_count"] == 1
        and owner["atom_body_tag"] == 0
        and owner["activation_mark"] < owner["selected_mark"],
        "part did not retain the actual selected import, atom and rollback owners",
    )
    header, nodes, offsets = read_typed(kernel)
    verify_graph(nodes)
    raw_projection = make_neutral(nodes, offsets)
    require(
        write_typed(header, nodes) == kernel
        and intake.brep is None
        and DecodeBrepModel(kernel) is None,
        "typed periodic kernel or exact selected payload replay differs",
    )
    document = open_document(
        part.BytesValue,
        source_format="solidworks.sldprt",
        strict=True,
        include_tessellation=False,
    )
    converted = document.brep
    require(
        converted is not None and document.brep_payloads == intake.brep_payloads,
        "strict read did not select the generated kernel",
    )
    (body,) = document.bodies
    (solid,) = converted.bodies
    (feature,) = (
        item for item in document.feature_timeline if item.kind is FeatureKind.IMPORTED
    )
    require(
        body.id == solid.design_body_id == "sldprt:body:1"
        and body.final_feature_id
        == feature.id
        == f"sldprt:feature:{owner['feature_id']}"
        and feature.operation is None
        and not feature.parameter_ids
        and not document.parameters
        and all(entry.severity is Severity.INFO for entry in document.diagnostics)
        and not converted.validate(frozenset({body.id})),
        "portable solid did not reconstruct its actual native owner and geometry",
    )
    counts, measured = measure_neutral(
        replace(converted, bodies=(replace(solid, design_body_id=""),))
    )
    compare_measures(measured, expected, "strict generated shape")
    compare_seams(source, converted)
    require(
        sorted(len(loop.coedge_ids) for loop in source.loops)
        == sorted(len(loop.coedge_ids) for loop in converted.loops)
        and sorted(loop.outer for loop in source.loops)
        == sorted(loop.outer for loop in converted.loops),
        "a qualified source rim changed its neutral loop role",
    )
    return {
        "part": fingerprint(part.BytesValue),
        "local_kernel": fingerprint(kernel),
        "owned_archive": owner,
        "counts": counts,
        "measured": measured,
        "resident_nodes": len(nodes),
        "exact_full_turn_intervals": len(converted.edges),
        "projected_endpoint_intervals": [
            (edge.start_parameter, edge.end_parameter) for edge in raw_projection.edges
        ],
        "streams": {
            name: fingerprint(value) for name, value in archive.streams.items()
        },
    }


def verify_disclosed(name, model, evidence):
    boundary = author_boundary(model)
    actual = construct(neutral_document(boundary), name)
    historical, _, labels, settings, scene = research_part(
        model, NATIVE_PATH / (name + ".SLDPRT")
    )
    require(
        actual.BytesValue == historical.BytesValue
        and actual.StreamsValue == historical.StreamsValue
        and fingerprint(actual.BytesValue)
        == {
            "bytes": evidence["generated_bytes"],
            "sha256": evidence["generated_sha256"],
        },
        f"{name} does not reproduce the frozen native part",
    )
    result = verify_part(actual, boundary, expected_measures(model))
    geometry = evidence["native_reopened_geometry"]
    require(
        (geometry["solids"], geometry["faces"], geometry["edges"], geometry["vertices"])
        == (1, 3, 2, 0),
        "native receipt has a different source topology",
    )
    compare_measures(
        result["measured"],
        {
            "volume_mm3": geometry["volume_m3"] * 10**9,
            "area_mm2": geometry["area_m2"] * 10**6,
            "centroid_mm": tuple(value * 1000 for value in geometry["com_m"]),
            "bounds_mm": tuple(
                tuple(value * 1000 for value in corner)
                for corner in geometry["extreme_bounds_m"]
            ),
        },
        "prior disclosed native geometry",
    )
    return result, actual, (labels, settings, scene)


def compare_planar(cylinder, inputs):
    from BuildLocalBodyKernel import CASES as PRISMS, prism_model

    labels, settings, scene = inputs
    points, levels, _ = PRISMS["Rectangular"]
    boundary = prism_model("IndependentPlanarControl", points, levels)
    planar = MakeBareImport(
        neutral_document(boundary), settings, labels, AmbientValue=scene
    )
    differing = sorted(
        name
        for name in planar.StreamsValue
        if planar.StreamsValue[name] != cylinder.StreamsValue[name]
    )
    restored = open_document(
        planar.BytesValue,
        source_format="solidworks.sldprt",
        strict=True,
        include_tessellation=False,
    )
    require(
        differing == [KLocalBodyStream]
        and restored.brep is not None
        and len(restored.brep.faces) == 6,
        "same-locator planar control changed shared archive or geometry",
    )
    return fingerprint(planar.BytesValue)


def variants():
    boundary = author_boundary(OBLIQUE)
    document = neutral_document(boundary)
    shifted = replace(
        boundary.vertices[0],
        point=SpaceVector(
            boundary.vertices[0].point.x + 0.5,
            boundary.vertices[0].point.y,
            boundary.vertices[0].point.z,
        ),
    )
    far_curve = boundary.curves[0]
    rotated = replace(
        far_curve, reference_direction=negate(far_curve.reference_direction)
    )
    rotated_seam = replace(
        boundary.vertices[0],
        point=OffsetVector(rotated.center, rotated.reference_direction, rotated.radius),
    )
    alternate = replace(
        boundary,
        curves=(rotated, boundary.curves[1]),
        vertices=(rotated_seam, boundary.vertices[1]),
    )
    shortened = replace(
        boundary,
        edges=(replace(boundary.edges[0], end_parameter=tau / 2), boundary.edges[1]),
    )
    wrong_use = replace(
        boundary,
        coedges=(replace(boundary.coedges[0], reversed=False), *boundary.coedges[1:]),
    )
    wrong_radius = replace(
        boundary,
        surfaces=(
            replace(boundary.surfaces[0], radius=OBLIQUE.radius_mm * 1.02),
            *boundary.surfaces[1:],
        ),
    )
    second_curve = replace(boundary.curves[1], id="unowned-orbit")
    extra_curve = replace(boundary, curves=(*boundary.curves, second_curve))
    for name, shape in (
        ("shifted_seam", replace(boundary, vertices=(shifted, boundary.vertices[1]))),
        ("other_seam_frame", alternate),
        ("partial_trim", shortened),
        ("wrong_rim_owner_sense", wrong_use),
        ("wrong_mantle_radius", wrong_radius),
        ("unowned_carrier", extra_curve),
    ):
        yield name, replace(document, brep=shape)
    yield "unowned_source_metadata", replace(document, metadata={"unsupported": "keep"})
    yield "extra_configuration", replace(
        document,
        configurations=(
            *document.configurations,
            Configuration("other", "Other", False),
        ),
    )


def refusal_checks():
    refused = {}
    for name, document in variants():
        try:
            construct(document, "Refusal")
        except ValueError as error:
            refused[name] = str(error)
        else:
            raise ValueError(
                f"unsupported geometry or source domain was consumed: {name}"
            )
    return refused


def verify_oblique():
    boundary = author_boundary(OBLIQUE)
    original = construct(neutral_document(boundary), "Oblique")
    result = verify_part(original, boundary, expected_measures(OBLIQUE))
    permuted = replace(
        boundary,
        faces=boundary.faces[::-1],
        coedges=boundary.coedges[::-1],
        curves=boundary.curves[::-1],
    )
    require(
        construct(neutral_document(permuted), "Oblique").BytesValue
        == original.BytesValue,
        "unowned collection order affected canonical wire allocation",
    )
    variant = replace(OBLIQUE, radius_mm=OBLIQUE.radius_mm + 0.625)
    modified_shape = author_boundary(variant)
    modified_part = construct(neutral_document(modified_shape), "Oblique")
    modified = verify_part(modified_part, modified_shape, expected_measures(variant))
    require(
        original.StreamsValue.keys() == modified_part.StreamsValue.keys()
        and len(original.StreamsValue[KLocalBodyStream])
        != len(modified_part.StreamsValue[KLocalBodyStream])
        and [
            name
            for name in original.StreamsValue
            if original.StreamsValue[name] != modified_part.StreamsValue[name]
        ]
        == [KLocalBodyStream],
        "changing authored radius affected another stream or failed to update the periodic payload",
    )
    return {
        "original": result,
        "altered_radius": modified,
        "bare_local_only_changed": True,
    }


def main():
    lifecycle_bytes = (MEASUREMENTS / LIFECYCLE).read_bytes()
    lock_bytes = (MEASUREMENTS / LOCK).read_bytes()
    planar_bytes = (MEASUREMENTS / PLANAR_REFERENCE).read_bytes()
    native, sealed = map(json.loads, (lifecycle_bytes, lock_bytes))
    planar_reference = json.loads(planar_bytes)["cases"]
    require(
        native["controls_healthy"]
        and native["disclosed_native_part_lifecycles"] == 2
        and sealed["passed"]
        and sealed["heldout_sources_locked"] == 2
        and sealed["heldout_payloads_shared"] == 0,
        "expected disclosed lifecycle and opaque prospective source lock",
    )
    sources = (
        *sorted((ARCHIVE / "Partition/LocalCylinder").glob("*.py")),
        *(
            ARCHIVE / name
            for name in (
                "Construction/Part/Imports/MakeBareImport.py",
                "Partition/LocalPrism/MakeBoundRoot.py",
                "Partition/LocalPrism/MakePrismRoot.py",
                "Partition/LocalPrism/PrismNullFields.py",
                "Partition/LocalWrite/EncodeLocalXmt.py",
                "Partition/LocalWrite/LocalXmtProfile.py",
            )
        ),
        ROOT
        / "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/Cylinder/ReadLocalCyl.py",
        Path(__file__),
    )
    digests = {
        str(path.relative_to(ROOT)): fingerprint(path.read_bytes())["sha256"]
        for path in sources
    }
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "cp1252"):
        lookup(codec)
    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
    ):
        import_module(module)
    with guard_build():
        cases = {}
        planar = {}
        for name, model in CASES.items():
            cases[name], cylinder, inputs = verify_disclosed(
                name, model, native["cases"][name]
            )
            planar[name] = compare_planar(cylinder, inputs)
            require(
                planar[name] == planar_reference[name]["planar_control"]["part"],
                "the prior same-locator planar archive changed",
            )
        oblique = verify_oblique()
        refused = refusal_checks()
    print(
        json.dumps(
            {
                "schema": "kit.sw2026.model-to-local-cylinder.v1",
                "source_lock": fingerprint(lock_bytes),
                "native_disclosed_lifecycle": fingerprint(lifecycle_bytes),
                "prior_planar_reference": fingerprint(planar_bytes),
                "serializers": digests,
                "disclosed_exact": cases,
                "same_locator_planar": planar,
                "independent_oblique": oblique,
                "refused": refused,
                "runtime_reads": 0,
                "guest_private_sources_read": 0,
                "native_processes_started": 0,
                "public_writer_admitted": False,
            },
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
