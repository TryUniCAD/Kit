from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import dist, isclose
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]
from EllipseModel import predict
from VerifyEllipseBoundary import check_measures
from convert import open_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

TRIAL_SHA = "5a0cb6cfe063ac3357e193c5d39ca1749f16ad26ef6e995fdb2cae0ce5244653"
DISCLOSED_RESULT = "6c71cfd01e4b681856a4bd0aaf81d6ef7d2a10af4be1bc4feb4e6bce795d2c93"
FORMAT = "solidworks.sldprt"


def hash_bytes(value):
    return sha256(value).hexdigest()


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def read_semantics(data, case, include_brep):
    result = open_document(BytesIO(data), source_format=FORMAT, include_brep=include_brep, configuration="Default", strict=True)
    restored = CadDocument.from_json(result.to_json())
    demand(not restored.validate() and result.to_json() == restored.to_json()
           and (result.brep is not None) == include_brep and not result.brep_payloads,
           "neutral conic round trip or B-rep option differs")
    feature, = (step for step in result.feature_timeline if step.kind == FeatureKind.KExtrusion)
    sketch, = result.sketches
    entity, = sketch.entities
    driver, = result.parameters
    body, = result.bodies
    geom = entity.geometry
    intended = predict(case)
    demand(type(geom) is EllipseGeometry and not entity.construction and not entity.fixed
           and sketch.closed_profile_entity_ids == ((entity.id,),) and not sketch.constraints
           and not sketch.parameter_ids and result.metadata["solidworks.typed_resolved_semantics"]["ellipse_point_ids"] == (2, 1, 3, 4, 5, 6)
           and entity.provenance.confidence == 1.0 and len(entity.provenance.spans) == 1,
           "inline ellipse and distinct seam ownership not recovered")
    actual = ((geom.center.x, geom.center.y), (geom.major_axis.x, geom.major_axis.y), (geom.major_radius, geom.minor_radius))
    expected = (case["center_mm"], intended["unit_axes"][0][:2], case["radii_mm"])
    demand(all(dist(a, b) < 1e-11 for a, b in zip(actual, expected, strict=True)),
           "closed ellipse differs from independent model dimensions or signed orientation")
    demand(type(feature.definition) is ExtrudeFeature and feature.definition.end_condition == ExtrudeEnd.KBlind
           and not feature.definition.reversed and feature.definition.second_length is None
           and feature.operation == BooleanOp.KCreate and feature.sketch_id == sketch.id
           and feature.parameter_ids == (driver.id,) and feature.definition.length == driver.value
           and (driver.name, driver.role, driver.owner_id) == ("D1", ParameterRole.KDriving, feature.id)
           and isclose(driver.value.value, case["depth_mm"], rel_tol=1e-14) and driver.provenance.confidence == 1.0
           and body.final_feature_id == feature.id and body.name == feature.name == "EllipseBoss"
           and len(result.feature_timeline) == 19
           and next(plane.name for plane in result.support_planes if plane.id == sketch.support_plane_id) == "Front Plane",
           "ellipse read lost the ordinary support, parametric boss or live depth")
    return result


def missing_cache(data, *, raw=False):
    try:
        if raw:
            SldprtAdapter().read(BytesIO(data), ReadOptions(extract_raw_brep=True))
        else:
            open_document(BytesIO(data), source_format=FORMAT, strict=True)
    except SldprtFormat as error:
        demand("no readable Parasolid payload" in str(error), "ellipse geometry boundary changed")
    else:
        raise ValueError("ellipse unexpectedly publishes strict geometry")


def broken_models(archive):
    for label in ("distinct_endpoint", "crossed_axis_role", "foreign_handle", "changed_point_style", "reversed_boss"):
        link = ReadNativeLink(archive, 0, ReadEllipses=True)
        profile, boss = link.ResolvedValue.RootsValue[-2:]
        sketch = profile.FieldsValue["pd_f80"].FieldsValue
        ellipse = sketch["ellipses"][0]["ellipse"]
        if label == "distinct_endpoint":
            ellipse["fcc_s"] = ellipse["fe0_s"]
        elif label == "crossed_axis_role":
            ellipse["fe0_s"], ellipse["fe4_s"] = ellipse["fe4_s"], ellipse["fe0_s"]
        elif label == "foreign_handle":
            sketch["points"][ellipse["fc8_s"]]["point"]["h1"].FieldsValue["f08"] = 1
        elif label == "changed_point_style":
            sketch["points"][ellipse["fdc_s"]]["point"]["lw"]["f00"] = .25
        else:
            boss.FieldsValue["f818"].FieldsValue["f8c"] = 1
        graph = link.ResolvedValue
        changed, _ = WriteResolMut(graph.RootsValue, graph.ExtraFields, 19000, link.ConfigValue.MapValue,
                                   graph.ContextValue, ReplayEllipses=True)
        streams = dict(archive.Streams)
        streams[link.StreamName] = changed
        data = BuildSldprt(streams, FormatVersion=4)
        document = open_document(BytesIO(data), source_format=FORMAT, include_brep=False, strict=True)
        demand(not any(isinstance(entity.geometry, EllipseGeometry) for profile in document.sketches for entity in profile.entities)
               and document.metadata["solidworks.typed_resolved_semantics"]["status"] == "unsupported",
               "ineligible ellipse received a typed portable contour")
        missing_cache(data)
        yield label


def worker(request, raw):
    if request.get("contrast"):
        missing_cache(raw, raw=True)
        return {"refusals": [*broken_models(SldprtArchive.FromBytes(raw)), "raw_brep_request"]}
    audit = BuildAudit(HERE.parents[1] / "serial/defs")
    sys.addaudithook(audit.InspectEvent)
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    audit.BeginBuild()
    document = read_semantics(raw, request["case"], False)
    full = read_semantics(raw, request["case"], True)
    demand(full.sketches == document.sketches and full.parameters == document.parameters
           and full.feature_timeline == document.feature_timeline,
           "default and no-Brep read changed the exact conic and driver semantics")
    checked, measures = check_measures(full, request["case"], request["cold_native"])
    demand(not audit.DeniedReads and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "ellipse readback accessed external data or the native runtime")
    return {"archive_sha256": hash_bytes(raw), "profile": "closed_signed_ellipse",
            "public_root_features": len(document.feature_timeline), "driver": "D1",
            "distinct_sketch_point_owners": 6, "runtime_accesses": 0,
            "strict_geometry": "exact_rational_full_ellipse",
            "native_initial_metrics": measures,
            "independent_trim_surface_evaluations": checked}


def native_receipt(native):
    terminal = json.loads(native.read_bytes())
    demand(terminal["passed"] and terminal["fresh_processes"] == 8 and terminal["healthy_controls"] is True
           and sum(phase["control"] is not None for phase in terminal["phases"]) == 4
           and terminal["oracle_build"] == "34.5.2.0604", "disclosed native controls or exact build differ")
    originals = {}
    receipts = {}
    for phase in terminal["phases"]:
        slot = phase["slot"]
        tag = f"Slot{slot + 1:02}" if slot is not None else Path(phase["control"]).stem
        locator = f"{phase['phase']}-{tag}.json"
        raw = (native.parent / "DisclosedPhases" / locator).read_bytes()
        demand(hash_bytes(raw) == phase["receipt_sha256"] and phase["passed"] and phase["exit_code"] == 0,
               "disclosed native phase changed")
        receipts[locator] = phase["receipt_sha256"]
        if phase["phase"] == "edit":
            record = json.loads(raw)
            demand(record["open_status"] == {"opened": True, "errors": 0, "warnings": 0} and record["passed"],
                   "cold native observation failed")
            body = record["cold"]["body"]
            originals[slot] = {key: body["mass"][key] for key in ("volume", "area", "com", "accuracy_level")} | {
                "solid_count": body["solid_count"], "faces": body["faces"], "bounds_m": body["bounds_m"],
                "seams_m": [cap["trim"]["seam_points_m"][0] for cap in sorted(body["caps"], key=lambda cap: cap["station"])],
                "archive_sha256": record["job"]["source_sha256"],
            }
    return originals, receipts


def read_controls(trial, frozen):
    result = {}
    for label in ("ControlCircle.SLDPRT", "ControlRectangle.SLDPRT"):
        data = (trial.parent / label).read_bytes()
        checksum = hash_bytes(data)
        demand(checksum == frozen["files"][label]["sha256"], "legacy native control differs")
        full = open_document(BytesIO(data), source_format=FORMAT, strict=True)
        design = open_document(BytesIO(data), source_format=FORMAT, include_brep=False, strict=True)
        demand(full.brep is not None and not full.validate() and design.brep is None
               and not design.validate() and len(full.bodies) == len(design.bodies) == 1 and
               not any(isinstance(entity.geometry, EllipseGeometry) for profile in design.sketches for entity in profile.entities),
               "existing rectangle or circular public read changed")
        result[label] = {"sha256": checksum, "faces": len(full.brep.faces)}
    return result


def supervise(trial, native, output):
    trial_raw = trial.read_bytes()
    demand(hash_bytes(trial_raw) == TRIAL_SHA and hash_bytes(native.read_bytes()) == DISCLOSED_RESULT,
           "exact native-tested source authorities differ")
    frozen = json.loads(trial_raw)
    originals, receipts = native_receipt(native)
    controls = read_controls(trial, frozen)
    results = []
    for slot, (case, row) in enumerate(zip(frozen["spec"]["cases"], frozen["candidates"], strict=True)):
        candidate = trial.parent / row["path"]
        checksum = hash_bytes(candidate.read_bytes())
        demand(checksum == row["proof"]["archive_sha256"] == originals[slot]["archive_sha256"], "measured cold archive changed")
        request = {"case": case, "candidate": str(candidate), "cold_native": originals[slot]}
        result = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                                input=json.dumps(request).encode(), capture_output=True, check=False)
        demand(result.returncode == 0 and not result.stderr, result.stderr.decode())
        payload = json.loads(result.stdout)
        demand(payload["archive_sha256"] == checksum, "worker read a different source")
        negative = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                                  input=json.dumps(request | {"contrast": True}).encode(),
                                  capture_output=True, check=False)
        demand(negative.returncode == 0 and not negative.stderr, negative.stderr.decode())
        results.append(payload | json.loads(negative.stdout) | {"case": case["name"]})
    root = ROOT / "src/convert/adapters/solidworks/Core"
    paths = {*((root / "TypedResolved/Ellipses").rglob("*.py")), root / "Adapter.py",
             root / "TypedResolved/Geometry/CheckPrismMgr.py", root / "TypedResolved/Geometry/Display/ReadGeomMessage.py"}
    evidence = {"trial_sha256": TRIAL_SHA, "disclosed_result_sha256": DISCLOSED_RESULT,
                "method_sha256": hash_bytes(HERE.read_bytes()),
                "boundary_proof_sha256": hash_bytes(HERE.with_name("VerifyEllipseBoundary.py").read_bytes()),
                "native_phase_sha256": receipts, "legacy_controls": controls,
                "reader_paths": {path.relative_to(ROOT).as_posix(): hash_bytes(path.read_bytes()) for path in sorted(paths)},
                "guarded_processes": len(results), "contrast_processes": len(results),
                "native_launches": 0, "heldout_credit": 0, "results": results}
    with output.open("x") as stream:
        json.dump(evidence, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": hash_bytes(output.read_bytes()), "cases": len(results)}))


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--worker", action="store_true")
    cli.add_argument("--trial", type=Path)
    cli.add_argument("--native", type=Path)
    cli.add_argument("--output", type=Path)
    args = cli.parse_args()
    if args.worker:
        request = json.load(sys.stdin)
        print(json.dumps(worker(request, Path(request["candidate"]).read_bytes())))
    else:
        supervise(args.trial, args.native, args.output)
