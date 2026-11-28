from argparse import ArgumentParser
from codecs import lookup
from contextlib import nullcontext
from dataclasses import replace
from importlib import import_module
from io import BytesIO
import json
from math import pi
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from SealedCylinderModel import geometry_document
from VerifyBareImportPackage import fingerprint, guard_build, require
from convert import open_document, write_document
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Revolve.SweepVector import OffsetVector
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordProvenance import Provenance

ROOT = Path(__file__).resolve().parents[4]
NATIVE_RECEIPT = (
    ROOT / "re/solidworks/measurements/2026/GeneratedLocalCylinderPartNative01.json"
)
NATIVE_IDENTITY = r"C:\KitCylinderPart01\Candidates\TranslatedZ.SLDPRT"
EPOCH = 1790000000
SPEC = {
    "face_center_m": [0.01625, -0.0085, 0.003375],
    "axis": [0.0, 0.0, 1.0],
    "radius_m": 0.00675,
    "height_m": 0.017125,
}
OBLIQUE = {
    "face_center_m": [-0.007125, 0.013375, 0.024625],
    "axis": [2 / 3, -1 / 3, 2 / 3],
    "radius_m": 0.0059375,
    "height_m": 0.0325,
}
FORMAT = "solidworks.sldprt"
EMITTER = "convert.adapters.solidworks.Core.Writing.EmitNativeMut"
CAPS = frozenset({Capability.KBrep, Capability.KConfigurations})


def warm():
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "cp1252"):
        lookup(codec)
    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)


def guarded_prepare(*args, **kwargs):
    with guard_build():
        return PrepareNative(*args, **kwargs)


def exact_replay(document, evidence):
    staged = Path("/unused-periodic-stage/TranslatedZ.SLDPRT")
    options = WriteOptions(values={"final_destination": NATIVE_IDENTITY})
    first = guarded_prepare(document, staged, EPOCH, options)
    second = guarded_prepare(document, staged, EPOCH, options)
    identity = fingerprint(first.BytesValue)
    expected = {
        "bytes": evidence["generated_bytes"],
        "sha256": evidence["generated_sha256"],
    }
    require(
        first.BytesValue == second.BytesValue, "frozen preparation is nondeterministic"
    )
    require(
        identity == expected,
        f"frozen preparation produced {identity}, expected {expected}",
    )
    require(
        len(first.StreamsValue) == 12, "frozen periodic part lost its stream inventory"
    )
    return identity


def shifted_rim(model, center):
    far, near = model.curves
    cylinder, cap, base = model.surfaces
    seam, other = model.vertices
    return replace(
        model,
        curves=(replace(far, center=center), near),
        surfaces=(cylinder, replace(cap, origin=center), base),
        vertices=(
            replace(
                seam, point=OffsetVector(center, far.reference_direction, far.radius)
            ),
            other,
        ),
    )


def stretched_axes(model):
    far, near = model.curves
    cylinder, cap, base = model.surfaces
    forward, reverse = SpaceVector(0, 0, 2), SpaceVector(0, 0, -2)
    return replace(
        model,
        curves=(replace(far, axis=reverse), replace(near, axis=forward)),
        surfaces=(
            replace(cylinder, axis=forward),
            replace(cap, normal=forward),
            replace(base, normal=reverse),
        ),
    )


def planar_control():
    points = tuple(
        PlaneVector(*point) for point in ((1.0, -3.0), (20.0, -5.0), (14.0, 7.0))
    )
    segments = tuple(
        LineGeometry(first, second)
        for first, second in zip(points, points[1:] + points[:1], strict=True)
    )
    model, *_ = BuildPrism("outside-periodic", KTransformIdentity, segments, 3.0, 17.0)
    (body,) = model.bodies
    return replace(model, bodies=(replace(body, design_body_id=""),))


def variants(document):
    model = document.brep
    far, near = model.curves
    edge, other = model.edges
    assert isinstance(far.center, SpaceVector)
    assert isinstance(near.center, SpaceVector)
    wrong_owner = replace(
        far, provenance=Provenance("solidworks.sldprt", "external-rim")
    )
    separated = OffsetVector(far.center, SpaceVector(1, 0, 0), 0.25)
    reversed_station = OffsetVector(near.center, SpaceVector(0, 0, 1), -17.125)
    return {
        "off_axis_rim": replace(document, brep=shifted_rim(model, separated)),
        "reversed_span": replace(document, brep=shifted_rim(model, reversed_station)),
        "zero_span": replace(document, brep=shifted_rim(model, near.center)),
        "non_unit_axis": replace(document, brep=stretched_axes(model)),
        "partial_rim": replace(
            document,
            brep=replace(model, edges=(replace(edge, end_parameter=pi), other)),
        ),
        "closed_planar_solid": replace(document, brep=planar_control()),
        "geometry_provenance": replace(
            document, brep=replace(model, curves=(wrong_owner, near))
        ),
        "source_file_identity": replace(
            document, source=replace(document.source, path="external.part")
        ),
        "source_properties": replace(document, metadata={"author": "document owner"}),
        "extra_configuration": replace(
            document,
            configurations=(
                *document.configurations,
                replace(
                    document.configurations[0], id="second", name="Other", active=False
                ),
            ),
        ),
    }


def refused(action, error_types):
    try:
        action()
    except error_types as error:
        return str(error)
    raise ValueError("unqualified periodic request succeeded")


def check_target(target, expected):
    require(
        target.read_bytes() == expected, "a refused request changed the published part"
    )
    require(
        tuple(target.parent.iterdir()) == (target,),
        "unexpected staged or companion output",
    )


def check_refusals(writer, document, target):
    expected = target.read_bytes()
    wrong_targets = {}
    for name, changed in variants(document).items():
        require(not writer.supports(changed, target), f"selection admitted {name}")
        refused(lambda: write_document(changed, target, overwrite=True), NotFoundError)
        wrong_targets[name] = refused(
            lambda: writer.write(changed, target, WriteOptions(overwrite=True)),
            ValueError,
        )
        check_target(target, expected)
    for key, options in (
        ("wrong_selected_configuration", {"configuration": "unknown"}),
        ("caller_light_option", {"values": {"ambient": "caller override"}}),
    ):
        wrong_targets[key] = refused(
            lambda: write_document(document, target, overwrite=True, **options),
            ValueError,
        )
        absent = target.parent / key / target.name
        refused(lambda: write_document(document, absent, **options), ValueError)
        require(
            not absent.parent.exists(),
            "failed preparation left a destination directory",
        )
        check_target(target, expected)
    binary = BytesIO(b"existing")
    wrong_targets["binary_target"] = refused(
        lambda: write_document(
            document,
            binary,
            destination_format=FORMAT,
            values={"final_destination": NATIVE_IDENTITY},
        ),
        NotFoundError,
    )
    require(
        binary.getvalue() == b"existing", "binary refusal changed the caller stream"
    )
    assembly_target = target.with_suffix(".SLDASM")
    wrong_targets["assembly_destination"] = refused(
        lambda: write_document(document, assembly_target, destination_format=FORMAT),
        NotFoundError,
    )
    require(
        not assembly_target.exists(), "a part request wrote an assembly destination"
    )
    wrong_targets["staged_basename_mismatch"] = refused(
        lambda: guarded_prepare(
            document,
            target,
            EPOCH,
            WriteOptions(values={"final_destination": NATIVE_IDENTITY}),
        ),
        ValueError,
    )
    return wrong_targets


def publish(document, target, *, fixed_clock=True):
    writer = SldprtWriter()
    with guard_build():
        require(
            writer.supports(document, target),
            "public selection refused the periodic document",
        )
    clock_context = (
        patch(EMITTER + ".ReadTime", return_value=EPOCH)
        if fixed_clock
        else nullcontext()
    )
    with (
        patch(EMITTER + ".PrepareNative", side_effect=guarded_prepare) as prepare,
        clock_context as clock,
    ):
        result = write_document(document, target, allow_carrier=False)
        require(
            prepare.call_count == 1 and (clock is None or clock.call_count == 1),
            "public emit did not perform one guarded preparation",
        )
        written_at = prepare.call_args.args[2]
    payload = target.read_bytes()
    check_target(target, payload)
    require(
        result.path == target.resolve()
        and result.bytes_written == len(payload)
        and result.application_usable
        and result.vendor_loadable
        and not result.dropped
        and not result.requirements
        and len(result.transfers) == 2
        and result.native_capabilities == result.transferred_capabilities == CAPS
        and all(item.mode is TransferMode.KNative for item in result.transfers),
        "public result lost native capability accounting or staged path identity",
    )
    restored = open_document(
        payload, source_format=FORMAT, strict=True, include_tessellation=False
    )
    restored.assert_valid()
    (config,) = restored.configurations
    model = restored.brep
    (body,) = restored.bodies
    (feature,) = (
        item for item in restored.feature_timeline if item.kind is FeatureKind.KImported
    )
    require(
        config.name == document.configurations[0].name
        and config.active
        and feature.name == "Imported geometry"
        and model.bodies[0].design_body_id == body.id
        and (len(model.bodies), len(model.faces), len(model.edges), len(model.vertices))
        == (1, 3, 2, 2)
        and (
            body.topology.solid_count,
            body.topology.face_count,
            body.topology.edge_count,
        )
        == (1, 3, 2),
        "strict readback did not retain the periodic feature, configuration, and solid identity",
    )
    return {
        "part": fingerprint(payload),
        "native_caps": sorted(value.value for value in CAPS),
        "writer_epoch": written_at,
    }


def main():
    parser = ArgumentParser(
        description="Verify the public staged periodic SOLIDWORKS route"
    )
    parser.add_argument("--windows-output", type=Path)
    args = parser.parse_args()
    warm()
    oblique = geometry_document(OBLIQUE)
    oblique = replace(
        oblique, configurations=(replace(oblique.configurations[0], name="Inspection"),)
    )
    if args.windows_output is not None:
        target = args.windows_output
        require(
            os.name == "nt"
            and target.is_absolute()
            and not target.exists()
            and (not target.parent.exists() or not tuple(target.parent.iterdir())),
            "use an unused absolute Windows part destination in an empty directory",
        )
        evidence = {
            "schema": "kit.sw2026.public-periodic-cylinder-windows.v1",
            "windows_disclosed": publish(oblique, target, fixed_clock=False),
            "construction_runtime_input_reads": 0,
            "native_processes_started": 0,
        }
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return
    receipt = NATIVE_RECEIPT.read_bytes()
    native = json.loads(receipt)
    require(
        native["controls_healthy"] and native["distinct_native_processes"] == 10,
        "disclosed native controls did not qualify",
    )
    document = geometry_document(SPEC)
    exact = exact_replay(document, native["cases"]["TranslatedZ"])
    writer = SldprtWriter()
    with TemporaryDirectory(prefix="kit-public-periodic-") as directory:
        destination = Path(directory) / "public" / "ObliqueCylinder.SLDPRT"
        public = publish(oblique, destination)
        rejections = check_refusals(writer, document, destination)
    evidence = {
        "schema": "kit.sw2026.public-periodic-cylinder.v1",
        "frozen_accepted_archive": exact,
        "frozen_native_receipt": fingerprint(receipt),
        "staged_sdk": public,
        "rejections": rejections,
        "construction_runtime_input_reads": 0,
        "native_processes_started": 0,
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
