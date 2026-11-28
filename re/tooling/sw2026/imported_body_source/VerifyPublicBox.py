from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import product
import json
from math import prod
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent),
                str(HERE.parent.with_name("attached_top_box_source"))]

from BoxIncidence import box_incidence
from SealedCylinderModel import geometry_document
from VerifyBareImportPackage import fingerprint, guard_build, require
from VerifyPublicCyl import (
    CAPS, EMITTER, EPOCH, FORMAT, NATIVE_RECEIPT as CYLINDER_RECEIPT, OBLIQUE, SPEC,
    check_refusals as cylinder_refusals, check_target, exact_replay as cylinder_replay,
    guarded_prepare, planar_control, publish as publish_cylinder, refused, warm,
)
from convert import open_document, write_document
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Revolve.SweepVector import OffsetVector
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import MakeLocalPrism
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Imports.CheckImportGeo import HasBoxCorners
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument, CadSource, Configuration
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordProvenance import Provenance


RECEIPTS = ROOT / "re/solidworks/measurements/2026"
NATIVE_RECEIPT = RECEIPTS / "GeneratedLocalBodyPartCompleted01.json"
NATIVE_RECEIPT_SHA = "40d77a01a37e8d85517fbfa642a208bdcd3b29378d426021b643cbd909e1a6c4"
NATIVE_PATH = r"C:\KitImportedProbe03\Candidates\RectangularBare.SLDPRT"
DISCLOSED_BOUNDS = ((-9.0, 4.0), (5.0, 23.0), (3.0, 14.0))
STAGED_BOUNDS = ((-19.25, 2.375), (5.125, 36.75), (-12.25, 4.875))


def prism(points, stations):
    ring = tuple(PlaneVector(x, y) for x, y in points)
    lines = tuple(LineGeometry(a, b) for a, b in zip(ring, ring[1:] + ring[:1], strict=True))
    model, *_ = BuildPrism("geometry-only", KTransformIdentity, lines, *stations)
    body, = model.bodies
    return replace(model, bodies=(replace(body, design_body_id=""),))


def box_document(bounds, configuration="Default"):
    (left, right), (front, back), stations = bounds
    model = prism(((left, front), (right, front), (right, back), (left, back)), stations)
    return CadDocument(CadSource("kit.neutral", "", ""), (Configuration("active", configuration, True),),
                       (), (), (), (), (), (), brep=model)


def observed_box(payload, bounds, configuration, locator):
    archive = SldprtArchive.from_bytes(payload)
    require(archive.format_version == 4 and len(archive.records) == 12,
            "rectangular import did not retain its complete archive")
    for stream in ("Header2", "Contents/Config-0-ModelHeader"):
        header = ReadHeader(archive.require(stream), 19000)
        require(header.SelfFile.PathValue == locator, "part header lost final logical self identity")
    document = open_document(payload, source_format=FORMAT)
    body, = document.bodies
    config, = document.configurations
    feature, = (row for row in document.feature_timeline if row.kind == "imported")
    require(body.final_feature_id == feature.id and feature.name == body.name == "Imported geometry"
            and config.active and config.name == configuration and not document.validate(),
            "strict reader lost actual body, import or configuration ownership")
    expected = tuple(product(*bounds))
    solid_id, incidence = box_incidence(document.brep, expected, body.id)
    normals = sorted((plane.normal.x, plane.normal.y, plane.normal.z) for plane in document.brep.surfaces)
    require(set(normals) == {tuple(sign if i == axis else 0 for i in range(3))
                             for axis, sign in product(range(3), (-1, 1))},
            "strict box did not retain all six signed face normals")
    points = [tuple(getattr(row.point, axis) for axis in "xyz") for row in document.brep.vertices]
    observed = tuple((min(values), max(values)) for values in zip(*points, strict=True))
    require(observed == bounds, "strict readback geometry moved an authored box endpoint")
    a, b, c = (high - low for low, high in observed)
    return {"bound_solid": solid_id, "feature": feature.id, "design_body": body.id,
            "bounds_axis_pairs_mm": observed, "closed_incidence_counts": incidence["counts"],
            "signed_plane_normals": normals,
            "volume_mm3": prod((a, b, c)), "area_mm2": 2 * (a*b + b*c + c*a),
            "centroid_mm": tuple((low + high) / 2 for low, high in observed),
            "configuration": config.name, "stored_locator": locator}


def verified_receipt():
    raw = NATIVE_RECEIPT.read_bytes()
    require(sha256(raw).hexdigest() == NATIVE_RECEIPT_SHA, "disclosed native receipt changed")
    native = json.loads(raw)
    case = native["cases"]["RectangularBare"]
    require(native["controls_healthy"] and native["oracle_file_version"] == "34.5.2.0604"
            and case["initial_diagnostics"]["warning"] == case["reopen_diagnostics"]["warning"] == 0
            and case["persistent_feature_identity"], "existing geometry lifecycle does not qualify")
    return case


def exact_preparation():
    warm()
    prior = verified_receipt()
    document = box_document(DISCLOSED_BOUNDS)
    with guard_build() as audit:
        candidate = PrepareNative(document, NATIVE_PATH, EPOCH)
        artifact = fingerprint(candidate.BytesValue)
        require(artifact == {"bytes": prior["generated_bytes"], "sha256": prior["native_input_sha256"]}
                and {name: fingerprint(raw) for name, raw in candidate.StreamsValue.items()} == prior["generated_streams"],
                "ordinary preparation changed the native-tested rectangular bytes")
        geometry = observed_box(candidate.BytesValue, DISCLOSED_BOUNDS, "Default", NATIVE_PATH)
        require(geometry["volume_mm3"] == 2574.0 and geometry["area_mm2"] == 1150.0
                and geometry["centroid_mm"] == (-2.5, 14.0, 8.5),
                "native-tested rectangle disagrees with its measured boundary")
    return {"artifact": artifact, "exact_logical_streams": len(candidate.StreamsValue),
            "geometry": geometry, "writer_epoch": EPOCH, "runtime_data_reads": len(audit.DeniedReads)}


def publish_box(document, target):
    with guard_build():
        require(SldprtWriter().supports(document, target), "normal selection refused the closed rectangular solid")
    with (patch(EMITTER + ".PrepareNative", side_effect=guarded_prepare) as prepare,
          patch(EMITTER + ".ReadTime", return_value=EPOCH) as clock):
        result = write_document(document, target)
    payload = target.read_bytes()
    check_target(target, payload)
    source, stage, written_at, settings = prepare.call_args.args
    require(prepare.call_count == clock.call_count == 1 and source is document and written_at == EPOCH
            and stage.name == target.name and stage.parent != target.parent and stage.parent.parent == target.parent
            and settings.values["final_destination"] == str(target.resolve()),
            "ordinary registry did not select and publish its final staged destination")
    require(result.path == target.resolve() and result.bytes_written == len(payload)
            and not (result.dropped or result.requirements) and len(result.transfers) == 2
            and result.native_capabilities == result.transferred_capabilities == CAPS
            and all(item.mode is TransferMode.KNative for item in result.transfers),
            "stage did not account exactly for native boundary and configuration")
    with guard_build() as audit:
        geometry = observed_box(payload, STAGED_BOUNDS, document.configurations[0].name,
                                str(PureWindowsPath(r"C:\KitSdkCandidates") / target.name))
    return {"artifact": fingerprint(payload), "geometry": geometry, "exact_transfers": sorted(c.value for c in CAPS),
            "actual_staged_path": True, "runtime_data_reads": len(audit.DeniedReads)}


def rectangle_refusals(document, target):
    pristine = target.read_bytes()
    writer = SldprtWriter()
    model = document.brep
    triangle = planar_control()
    trapezoid = prism(((-9, 5), (4, 5), (7, 23), (-9, 23)), (3, 14))
    with guard_build():
        require(all(MakeLocalPrism(item) and not HasBoxCorners(item) for item in (triangle, trapezoid))
                and (len(trapezoid.faces), len(trapezoid.edges), len(trapezoid.vertices)) == (6, 12, 8),
                "negatives no longer isolate the exact rectangular admission")
    first_face, *other_faces = model.faces
    disconnected = replace(model, faces=(replace(first_face, loop_ids=other_faces[0].loop_ids), *other_faces))
    plane, *other_planes = model.surfaces
    offset = replace(plane, origin=OffsetVector(plane.origin, plane.normal, 2.0 ** -34))
    wrong_plane = replace(model, surfaces=(offset, *other_planes))
    with guard_build():
        require(HasBoxCorners(wrong_plane) and wrong_plane.vertices == model.vertices
                and wrong_plane.faces == model.faces and wrong_plane.edges == model.edges
                and MakeLocalPrism(wrong_plane) != MakeLocalPrism(model),
                "offset contrast must retain the box incidence and compile with a different plane")
    first_edge, *other_edges = model.edges
    marked = replace(model, edges=(replace(first_edge, provenance=Provenance("source", "edge")), *other_edges))
    require(HasBoxCorners(disconnected), "link corruption no longer tests the shared prism validator")
    requests = {
        "prior_triangle": replace(document, brep=triangle),
        "same_count_trapezoid": replace(document, brep=trapezoid),
        "unowned_face_loop": replace(document, brep=disconnected),
        "wrong_offset_plane": replace(document, brep=wrong_plane),
        "source_geometry_provenance": replace(document, brep=marked),
        "source_path": replace(document, source=replace(document.source, path="source.part")),
        "source_metadata": replace(document, metadata={"title": "Source document"}),
        "extra_configuration": replace(document, configurations=(*document.configurations,
                           Configuration("second", "Other", False))),
    }
    rows = {}
    for name, changed in requests.items():
        require(not writer.supports(changed, target), "selection admitted " + name)
        rows[name] = refused(lambda: write_document(changed, target, overwrite=True), NotFoundError)
        unused = target.parent / name / target.name
        refused(lambda: write_document(changed, unused), NotFoundError)
        require(not unused.parent.exists(), "rejected scope created a destination")
        check_target(target, pristine)
    require(refused(lambda: writer.write(requests["wrong_offset_plane"], target, WriteOptions(overwrite=True)),
                    ValueError) == "local box plane does not match its exact face station",
            "the shifted carrier did not refuse through the actual plane owner check")
    check_target(target, pristine)
    for name, options in (
        ("unowned_requested_configuration", {"configuration": "Other"}),
        ("caller_light", {"values": {"ambient": "caller option"}}),
    ):
        rows[name] = refused(lambda: write_document(document, target, overwrite=True, **options), ValueError)
        unused = target.parent / name / target.name
        refused(lambda: write_document(document, unused, **options), ValueError)
        require(not unused.parent.exists(), "refused settings left a staging or destination directory")
        check_target(target, pristine)
    stream = BytesIO(b"unchanged")
    rows["binary_target"] = refused(lambda: write_document(
        document, stream, destination_format=FORMAT, values={"final_destination": NATIVE_PATH}), NotFoundError)
    require(stream.getvalue() == b"unchanged", "stream refusal changed caller contents")
    assembly = target.with_suffix(".SLDASM")
    rows["assembly_target"] = refused(lambda: write_document(document, assembly, destination_format=FORMAT), NotFoundError)
    require(not assembly.exists(), "refused assembly path was written")
    return rows


def independent_exact():
    run = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--exact-worker"],
                         capture_output=True, text=True, timeout=120)
    require(run.returncode == 0 and not run.stderr, run.stderr or "independent exact replay failed")
    return json.loads(run.stdout)


def main():
    parser = ArgumentParser(description="Verify the guarded host rectangular native import path")
    parser.add_argument("--exact-worker", action="store_true")
    args = parser.parse_args()
    if args.exact_worker:
        print(json.dumps(exact_preparation(), sort_keys=True))
        return
    warm()
    first = independent_exact()
    require(first == independent_exact(), "two cold preparations differ")
    periodic_source = geometry_document(SPEC)
    native_periodic = json.loads(CYLINDER_RECEIPT.read_bytes())
    periodic = cylinder_replay(periodic_source, native_periodic["cases"]["TranslatedZ"])
    with TemporaryDirectory(prefix="kit-public-box-") as directory:
        folder = Path(directory).resolve()
        target = folder / "rectangular" / "TranslatedBox.SLDPRT"
        document = box_document(STAGED_BOUNDS, "Inspection")
        staged = publish_box(document, target)
        rejected = rectangle_refusals(document, target)
        cylinder_target = folder / "periodic" / "ObliqueCylinder.SLDPRT"
        cylinder = publish_cylinder(geometry_document(OBLIQUE), cylinder_target)
        prior_refusals = cylinder_refusals(SldprtWriter(), periodic_source, cylinder_target)
    result = {"schema": "kit.sw2026.rectangular-bare-import-host.v1", "passed": True,
              "exact_reference": first, "disclosed_native_receipt_sha256": NATIVE_RECEIPT_SHA,
              "exact_reference_processes": 2, "host_staged_read": staged, "rectangular_refusals": rejected,
              "periodic_exact_reference": periodic, "periodic_staged_control": cylinder,
              "unchanged_periodic_refusals": prior_refusals, "native_processes_started": 0,
              "new_native_lifecycles": 0, "bare_planar_heldout_lifecycles": 0}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
