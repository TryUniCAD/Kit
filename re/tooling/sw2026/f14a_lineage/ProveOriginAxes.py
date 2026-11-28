from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import product
from math import isclose
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
SW = ROOT / "src/convert/adapters/solidworks"
ATTACHED = HERE.parent.parent / "attached_top_box_source"
sys.path[:0] = [str(SW.parents[2]), str(ROOT), str(HERE.parent.parent), str(ATTACHED)]

from BoxIncidence import box_incidence, xyz
from VerifyAttachedAxisRead import changed_payload
from VerifyAttachedBoxAxes import replace_owner, source_object, with_value
from VerifyFreecadF14aIntact import NATIVE_REFUSAL, no_runtime_io, refused, wire
from VerifyOriginalFcstdAttachedBox import prewarm, refusal
from revolve.Preparation.RevolveStreamAudit02 import stream_audit
from convert import open_document, write_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import LowerBoxModel
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import PlanAttachedBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import PlanOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepOrigAxes import PrepOrigAxes
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepareBoxAxes import PrepareBoxAxes
from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import ProjectBoxAxes
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import ReadOriginAxes
from convert.adapters.solidworks.Core.Reading.ReadAdapter import NativePartModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadAxisGeom import ReadAxisGeom
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import ReadColdOutput
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.WithColdName import WithColdName
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Features.FeaturePlaneAxis import PlaneAxis

BASE = "e9b36b5d7e588d7f386477d8f4538ede2b523593"
SDK_TREE = "0a55ce0714e270bf7e0c5f38c7368181aa52a9eb"
MANIFEST = "e2053d84764ed9b65fc4bfe62f98b08c4d33bb57f096f3a4e9265e802e9288fa"
RECEIPTS = {
    "SdkFreecadF14aOriginPlan01": "feb0a35f8975ee7d9a74e2eb416068e1337f7071cd2ec1c4bfdb524e5943ac61",
    "SdkFreecadBoxReleaseNative01": "e87ae3d9520edcffd262b1dc2457b2bd4e5a70fe4ff34c1a1271079d5628b856",
    "AttachedBoxAxesCandidate01": "93189f21691fc1cd3ba0f26beb62541f85ac3f814ae68444d178f639099efe60",
    "AttachedBoxAxesNative01": "7df283cd1c0ea388f3a0675deb63ef37184eada40ebbd4cd0898628c9996d624",
}
CASES = {
    "recipe-1.0.2-F14a": ("Freecad102", "2690f8a7f26e9096c917f0e2d4b9d311985a52dc1153546471064525ba8f68df"),
    "recipe-1.1.4-F14a": ("Freecad114", "c79cd3693db356fdf0d81f367ce56dc57f15b74b3bd5833811f8170bb30377b8"),
    "recipe-0.21.2-F14c": ("Attached", "25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb"),
}
FILES = (
    "Archive/Construction/Datums/PrincipalAxes/FinishAxesPart.py",
    "Archive/Construction/Datums/PrincipalAxes/PutAxisViewsMut.py",
    "Core/Preparation/FreecadBox/PrepOrigAxes.py",
    "Core/Preparation/FreecadBox/PrepareBoxAxes.py",
    "Core/Preparation/FreecadBox/Source/ReadOriginAxes.py",
    "Core/TypedResolved/Geometry/Axes/CheckAxisViews.py",
    "Core/TypedResolved/Geometry/Axes/ReadAxisGeom.py",
)
DRIVERS = ("Length", "Width", "Height")
FORMAT = "solidworks.sldprt"
PARENTS = (("Top Plane", "Front Plane"), ("Front Plane", "Right Plane"), ("Right Plane", "Top Plane"))
AXIS_STREAMS = [
    "Contents/CMgr",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Header2",
    "swXmlContents/KeyWords",
]


def digest(data):
    return sha256(data).hexdigest()


def pinned(path, expected):
    assert path.is_file() and not path.is_symlink()
    data = path.read_bytes()
    assert digest(data) == expected, f"{path.name} differs from the disclosed pin"
    return data


def archive_report(data):
    archive = SldprtArchive.from_bytes(data)
    return {
        "bytes": len(data),
        "sha256": digest(data),
        "streams": {name: {"bytes": len(raw), "sha256": digest(raw)}
                    for name, raw in archive.streams.items()},
    }


def axis_geometry(data, *, front):
    archive = SldprtArchive.from_bytes(data)
    model = NativePartModel(archive, None)
    linked = ReadNativeLink(archive, model.active_configuration_id)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    return ReadAxisGeom(archive, linked, manager, model, ReadColdOutput(linked), "sldprt:body:1", FrontStock=front)


def exact_linked_streams(data):
    archive = SldprtArchive.from_bytes(data)
    config, metadata = stream_audit(archive, ReadNativeLink(archive, 0), compact_keywords=False)
    assert len(config) + len(metadata) == 10 and all(row["qualified"] for row in metadata.values())
    return sorted(config | metadata)


def typed_front(data):
    design = open_document(data, source_format=FORMAT, strict=True, include_brep=False)
    (body,) = design.bodies
    assert design.brep is None and not design.brep_payloads and body.id == "sldprt:body:1"
    geometry = axis_geometry(data, front=True)
    return WithColdName(
        replace(design, bodies=(replace(body, topology=geometry.TopologyValue),), brep=geometry.BrepValue),
        geometry,
    )


def verify_axes(document, source, ranges, dimensions):
    document.assert_valid()
    features = {row.id: row for row in document.feature_timeline}
    axes = [row for row in document.feature_timeline if type(row.definition) is PlaneAxis]
    picks = {row.id: row for row in document.selections}
    planes = {row.id: row for row in document.support_planes}
    labels = tuple(row.LabelValue for row in source.AxisValues)
    assert len(axes) == 3 and axes == list(document.feature_timeline[-3:])
    assert tuple(row.name for row in axes) == labels and source.RecordShown
    rows, all_picks = [], set()
    for index, (axis, bounds, parents, owner) in enumerate(zip(axes, ranges, PARENTS, source.AxisValues, strict=True)):
        start, end = xyz(axis.definition.StartMm), xyz(axis.definition.EndMm)
        assert axis.selection_ids == (axis.definition.FirstPlaneSelectionId, axis.definition.SecondPlaneSelectionId)
        expected = bounds[0] - 0.05 * (bounds[1] - bounds[0]), bounds[1] + 0.05 * (bounds[1] - bounds[0])
        assert all(isclose(value, wanted, rel_tol=0, abs_tol=1e-12)
                   for value, wanted in zip((start[index], end[index]), expected, strict=True))
        assert all(point[other] == 0 for point in (start, end) for other in range(3) if index != other)
        assert not axis.suppressed and axis.attributes["solidworks.native_axis_hidden"] is False and owner.RecordShown
        assert tuple(features[feature_id].name for feature_id in axis.input_feature_ids) == parents
        target = []
        for selection_id, feature_id in zip(axis.selection_ids, axis.input_feature_ids, strict=True):
            pick = picks[selection_id]
            (path,) = pick.path
            plane = planes[path.entity_id]
            assert selection_id not in all_picks and path.entity_kind == "support_plane"
            assert pick.name == plane.name == features[feature_id].name
            assert pick.query["native_target_id"] == features[feature_id].attributes["native_object_id"]
            assert pick.query["native_owner_id"] == axis.attributes["native_object_id"]
            assert pick.provenance.spans[0].stream == "Contents/Config-0-ResolvedFeatures"
            all_picks.add(selection_id)
            target.append({"feature": feature_id, "plane": plane.name, "selection": selection_id})
        rows.append({"source_id": owner.RecordId, "source_role": owner.RoleName, "name": axis.name,
                     "target_id": axis.id, "bounds_mm": [start, end], "target_parents": target})
    assert len(all_picks) == 6
    (body,) = document.bodies
    (solid,) = document.brep.bodies
    volume = dimensions[0] * dimensions[1] * dimensions[2]
    area = 2 * sum(dimensions[a] * dimensions[b] for a, b in ((0, 1), (0, 2), (1, 2)))
    topo = body.topology
    assert (topo.solid_count, topo.face_count, topo.edge_count, topo.vertex_count) == (1, 6, 12, 8)
    assert solid.design_body_id == body.id and features[body.final_feature_id].operation == "create"
    assert isclose(topo.volume, volume, rel_tol=1e-14) and isclose(topo.surface_area, area, rel_tol=1e-14)
    for index, point in enumerate((topo.bounding_box.minimum, topo.bounding_box.maximum)):
        assert all(isclose(actual, bounds[index], rel_tol=0, abs_tol=1e-12)
                   for actual, bounds in zip(xyz(point), ranges, strict=True))
    (sketch,) = document.sketches
    parameters = {row.name: row for row in document.parameters}
    assert set(parameters) == set(DRIVERS)
    driver_values = {name: parameters[name].value.value for name in DRIVERS}
    assert all(isclose(driver_values[name], size, rel_tol=0, abs_tol=1e-12)
               for name, size in zip(DRIVERS, dimensions, strict=True))
    assert [parameters[name].owner_id for name in DRIVERS] == [features[body.final_feature_id].input_feature_ids[0]] * 2 + [body.final_feature_id]
    assert {parameters[name].id for name in DRIVERS[:2]} == set(sketch.parameter_ids)
    return {"axes": rows, "body": body.name, "source_origin_id": source.OriginId,
            "creator_id": body.final_feature_id, "volume_mm3": topo.volume, "area_mm2": topo.surface_area,
            "drivers_mm": driver_values, "analytic_centroid_mm": [(low + high) / 2 for low, high in ranges]}


def origin_faults(document, locator, data):
    source_row = source_object(document, "Y_Axis")
    changed = replace_owner(document, with_value(source_row, "Label", "Other axis"))
    native_faults = {
        "crossed_wrappers": "cache free origin axis has crossed or nonprincipal supports",
        "coherent_old_endpoint": "cache free origin axis endpoints disagree with their finite support",
        "hidden_axis": "cache free origin axis has unsupported feature state",
        "foreign_creation": "cache free origin axes lack complete creation ownership",
    }
    faults = {key: refusal(lambda: axis_geometry(changed_payload(data, key), front=True), msg)
              for key, msg in native_faults.items()}
    faults["inauthentic_neutral_label"] = refusal(lambda: PrepOrigAxes(changed, locator), "FreeCAD origin datum owners disagree with the source archive")
    faults["wrong_stock_profile"] = refusal(lambda: axis_geometry(data, front=False), "cache free origin axes require the signed Top stock")
    faults["ordinary_full_reader_closed"] = refusal(lambda: open_document(data, source_format=FORMAT, strict=True), "SLDPRT contains no readable Parasolid payload")
    plane = source_object(document, "XZ_Plane")
    shifted = replace_owner(document, with_value(plane, "Placement", "2.0", key="Py"))
    faults["displaced_source_origin_plane"] = refusal(lambda: ReadOriginAxes(shifted, CheckPlanes=True),
                                                       "FreeCAD origin plane no longer matches its signed principal support")
    if source_row["transient_properties"]:
        bad = replace_owner(document, {**source_row, "transient_properties": []})
        faults["missing_documented_transient_status"] = refusal(lambda: ReadOriginAxes(bad), "FreeCAD origin datum has an unrepresented owner or property")
    return faults


def origin_build(document, request):
    plan = PlanOriginBox(document)
    stock = plan.PartSource
    source = ReadOriginAxes(document)
    sizes = stock.DimensionsValue
    box = tuple((0.0, size) for size in sizes)
    locator = request["prior"]["original_logical_destination"]
    old = MakeOriginBox(stock.ModelValue, locator, stock.CreationEpoch, stock.PropertiesValue, UnitsValue=stock.UnitsValue)
    old_report = archive_report(old.BytesValue)
    prior = request["native"]["generated"]
    assert old_report["sha256"] == prior["file_sha256"] == request["prior"]["generated_sha256"]
    for name, row in (prior["exact_critical_streams"] | prior["exact_version_metadata"]).items():
        assert row["byte_identity"] and old_report["streams"][name] == {"bytes": row["bytes"], "sha256": row["sha256"]}
    build = PrepOrigAxes(document, locator)
    portable = type(document).from_json(document.to_json(indent=None))
    assert PrepOrigAxes(portable, locator).BytesValue == build.BytesValue
    current = archive_report(build.BytesValue)
    assert set(current["streams"]) == set(old_report["streams"])
    different = sorted(name for name in current["streams"] if current["streams"][name] != old_report["streams"][name])
    assert different == AXIS_STREAMS
    read = typed_front(build.BytesValue)
    axis_rows = verify_axes(read, source, box, sizes)
    stock_read = open_document(old.BytesValue, source_format=FORMAT, strict=True)
    unit_report = "solidworks.typed_resolved_semantics"
    units = read.metadata[unit_report]["document_units"]
    assert units == stock_read.metadata[unit_report]["document_units"] == prior["normal_document_units"]
    for name in ("custom_properties", "document_summary"):
        assert read.metadata[name] == stock_read.metadata[name]
    assert read.bodies[0].name == stock_read.bodies[0].name == stock.SourceBodyName
    corners = tuple(product(*box))
    _, native_roles = box_incidence(read.brep, corners, read.bodies[0].id)
    _, source_roles = box_incidence(document.brep, corners, document.bodies[0].id)
    assert native_roles == source_roles and len(plan.SourceLineage.Elements) == 26
    faults = origin_faults(document, locator, build.BytesValue)
    contrast = independent_contrast(plan, source, request)
    point = [row for row in document.metadata["freecad"]["objects"] if row["type_id"] == "App::Point"]
    assert len(point) == int(request["role"] == "Freecad114")
    return {
        "model_only_build": current, "stock_native_control": old_report, "changed_streams": different,
        "typed_linked_stream_byte_replay": exact_linked_streams(build.BytesValue),
        "typed_readback": axis_rows, "independent_neutral_contrast": contrast,
        "source_boundary_roles_verified": len(plan.SourceLineage.Elements), "read_document_units": units,
        "source_origin_point_ids_without_native_point": [row["object_id"] for row in point],
        "refusals": faults, "neutral_json_regeneration_exact": True,
        "measured_stock_controls_reproduced": True, "native_candidate_qualified": False,
    }


def independent_contrast(plan, source, request):
    limits = (11.25, 24.5, 37.75) if request["role"] == "Freecad102" else (31.0, 12.75, 5.5)
    stock = plan.PartSource
    dims = tuple(value.id for value in plan.SourceDrivers)
    lower = LowerBoxModel(plan.SourceDocument, "NeutralAxisBox", dims, limits, DRIVERS, stock.SourceBodyName)
    positive = PrepareBoxAxes(lower, r"C:\KitFreecadAxesContrast\NeutralAxisBox.SLDPRT", stock.CreationEpoch,
                              stock.PropertiesValue, ProjectBoxAxes(source), TopAttached=False, UnitsValue=stock.UnitsValue)
    read = typed_front(positive.BytesValue)
    result = verify_axes(read, source, tuple((0.0, size) for size in limits), limits)
    return {"sha256": digest(positive.BytesValue), "authored_sizes_mm": limits, "match": result}


def attached_control(document, request):
    plan = PlanAttachedBox(document)
    stock = plan.PartSource
    wanted = request["candidate"]
    locator = wanted["exact_guest_locator"]
    build = PrepareBoxAxes(stock.ModelValue, locator, stock.CreationEpoch, stock.PropertiesValue, ProjectBoxAxes(plan.OriginAxes))
    current = archive_report(build.BytesValue)
    assert current["sha256"] == wanted["candidate"]["sha256"] and current["bytes"] == wanted["candidate"]["bytes"]
    assert all(current["streams"][name] == row for name, row in wanted["candidate"]["streams"].items())
    read = open_document(build.BytesValue, source_format=FORMAT, strict=True)
    result = verify_axes(read, plan.OriginAxes, ((0, 20), (-10, 0), (0, 30)), (20, 30, 10))
    return {
        "existing_complete_native_hash_preserved": True, "archive": current, "typed_readback": result,
        "typed_linked_stream_byte_replay": exact_linked_streams(build.BytesValue),
    }


def writer_boundary(document, source, directory):
    target = directory / "F14a.SLDPRT"
    stream = BytesIO(b"the existing stream remains intact")
    stream.seek(4)
    initial = stream.tell(), stream.getvalue()
    writer = SldprtWriter()
    options = {"destination_format": FORMAT, "allow_carrier": False, "values": {"require_native_transfers": True}}
    with no_runtime_io():
        report = {
            "inferred_path": refused(lambda: write_document(document, target), NotFoundError, "no writer supports the destination", source),
            "explicit_path": refused(lambda: write_document(document, target, **options), ValueError, NATIVE_REFUSAL, source),
            "explicit_stream": refused(lambda: write_document(document, stream, **options), ValueError, NATIVE_REFUSAL, source),
            "direct_path": refused(lambda: writer.write(document, target), ValueError, NATIVE_REFUSAL, source),
        }
        assert not writer.supports(document, target)
    assert not list(directory.iterdir()) and initial == (stream.tell(), stream.getvalue())
    source_caps = GetDocumentCaps(document)
    return {
        "refusals": report, "empty_directory": True, "stream_unchanged": True,
        "source_capabilities": sorted(value.value for value in source_caps),
        "missing_from_adapter_capabilities": sorted(value.value for value in source_caps - writer.info.Capabilities),
    }


def worker(request):
    source = Path(request["path"])
    raw = pinned(source, request["sha256"])
    assert len(raw) == request["bytes"]
    document = open_document(source, strict=True, include_brep=True, include_tessellation=True)
    assert document.source.sha256 == request["sha256"]
    before = document.to_dict()
    prewarm()
    lookup("utf-8-sig")
    with no_runtime_io():
        output = (attached_control(document, request) if request["role"] == "Attached"
                  else origin_build(document, request))
    if request["role"] != "Attached":
        with TemporaryDirectory(prefix="KitOriginAxesRefusal.") as directory:
            output["public_write_boundary"] = writer_boundary(document, source, Path(directory))
    assert document.to_dict() == before and pinned(source, request["sha256"]) == raw
    return output | {"source_sha256": request["sha256"], "source_and_model_unchanged": True, "runtime_file_reads": 0}


def main(manifest):
    inventory = json.loads(pinned(manifest, MANIFEST))
    assert inventory["heldout_inputs"] == 0 and not inventory["original_corpus_membership_verified"]
    measure_root = ROOT / "re/solidworks/measurements/2026"
    receipts = {key: json.loads(pinned(measure_root / (key + ".json"), value)) for key, value in RECEIPTS.items()}
    old = receipts["SdkFreecadBoxReleaseNative01"]
    assert old["scoped_native_lifecycle_passed"] and len(old["healthy_control_records_sha256"]) == 2
    attached = receipts["AttachedBoxAxesNative01"]
    candidate = receipts["AttachedBoxAxesCandidate01"]
    assert attached["passed"] and attached["controls_healthy"] is True
    assert attached["candidate"]["sha256"] == candidate["candidate"]["sha256"]
    reports = {}
    for name, (role, pin) in CASES.items():
        (entry,) = (row for row in inventory["inputs"] if row["case"] == name)
        assert entry["sha256"] == pin
        request = dict(entry, role=role)
        if role == "Attached":
            assert attached["source_sha256"] == pin
            request["candidate"] = candidate
        else:
            (measured,) = (row for row in old["cases"] if row["role"] == role)
            assert measured["source_freecad_sha256"] == pin
            request["native"] = measured
            request["prior"] = receipts["SdkFreecadF14aOriginPlan01"]["cases"][name]
        records = []
        for _ in range(2):
            process = run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                          input=wire(request), capture_output=True, timeout=90)
            assert process.returncode == 0 and not process.stderr, process.stderr.decode(errors="replace")
            records.append(json.loads(process.stdout))
        assert records[0] == records[1]
        reports[name] = records[0]
    return {
        "schema": "kit.sw2026.freecad-origin-box-axes.v1", "base": BASE, "base_src_tree": SDK_TREE,
        "input_manifest_sha256": MANIFEST, "linked_prior_receipts_sha256": RECEIPTS,
        "changed_sdk_sha256": {path: digest((SW / path).read_bytes()) for path in FILES},
        "proof_tool_sha256": digest(HERE.read_bytes()),
        "reports": reports, "deterministic_worker_count": 6,
        "native_processes": 0, "new_native_acceptance": 0, "heldout_inputs": 0,
        "whole_source_publication": False, "corpus_credit": 0,
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        result = worker(json.load(sys.stdin))
    else:
        parser = ArgumentParser()
        parser.add_argument("disclosed_manifest", type=Path)
        result = main(parser.parse_args().disclosed_manifest)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
