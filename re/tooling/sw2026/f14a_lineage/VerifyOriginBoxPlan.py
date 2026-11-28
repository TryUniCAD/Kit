from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from VerifySdkBoxLineage import MANIFEST, NEGATIVE, POSITIVE, ROOT, pinned, refused


BASELINE = "ecbc50ee5f1721cac5d03dabb18da5f0afde0076"
NATIVE = "e87ae3d9520edcffd262b1dc2457b2bd4e5a70fe4ff34c1a1271079d5628b856"
INTACT = "89820d391925543775ea2ba05e56197ee0827a7ece06cd2451347985f540f9a4"
LINEAGE = "e85d804b20e71e8058e2f6b1e15151ea2f713e36afc859c8bf10729753a4695f"
DIMENSIONS = ("Length", "Width", "Height")
IDENTITY = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def frame(value):
    return tuple((row.x, row.y, row.z) for row in (value.origin, value.x_axis, value.y_axis, value.z_axis))


def placement(properties, key):
    node, = properties[key]["children"]
    assert node["tag"] == "PropertyPlacement"
    fields = node["attributes"]
    position = tuple(float(fields[name]) for name in ("Px", "Py", "Pz"))
    rotation = tuple(float(fields[name]) for name in ("Q0", "Q1", "Q2", "Q3"))
    assert position == IDENTITY[0] and rotation[:3] == IDENTITY[0] and abs(rotation[3]) == 1.0
    assert float(fields["A"]) == 0.0
    return {"origin_mm": position, "quaternion_xyzw": rotation}


def verify_source(plan, expected, retained):
    from VerifyFreecadF14aIntact import wire
    from interchange.document.Models.DocumentProvenance import IterProvenance

    document = plan.SourceDocument
    owner = plan.SourceLineage
    body, = document.bodies
    feature, = document.feature_timeline
    role_counts = Counter(row.KindValue for row in owner.Elements)
    owner_sha = sha256(wire(asdict(owner))).hexdigest()
    assert owner_sha == expected["owner_sha256"] and role_counts == expected["role_counts"]
    assert body.id == owner.BodyId and feature.id == owner.ProducerId and not document.selections
    assert plan.SourcePlane.id == "freecad:plane:XY_Plane"
    assert plan.SourcePlane in document.support_planes and plan.SourcePlacement == plan.SourcePlane.transform
    assert frame(plan.SourcePlacement) == IDENTITY
    properties = feature.definition.object_data["properties"]
    attachment, = properties["AttachmentSupport"]["children"]
    mode, = properties["MapMode"]["children"]
    assert attachment["attributes"] == {"count": "0"} and not attachment.get("children")
    assert mode["attributes"] == {"value": "0"}
    assert tuple(row.attributes["freecad_path"] for row in plan.SourceDrivers) == DIMENSIONS
    assert all(driver in document.parameters and driver.owner_id == feature.id for driver in plan.SourceDrivers)
    assert {row.id: sha256(row.data).hexdigest() for row in document.brep_payloads} == {
        owner_id: row["sha256"] for owner_id, row in retained["payloads"].items()
    }
    provenance = sorted(row.native_id for row in IterProvenance(document))
    assert provenance == retained["record_provenance_native_ids"]
    return {
        "source_sha256": owner.SourceSha256,
        "source_document_uuid": owner.DocumentUuid,
        "qualified_lineage_sha256": owner_sha,
        "source_owners": expected["source_owners"],
        "local_creator_role_counts": role_counts,
        "source_xy_frame": frame(plan.SourcePlacement),
        "source_xy_plane_id": plan.SourcePlane.id,
        "source_placements": {
            "body_placement": placement(body.attributes["freecad"]["properties"], "Placement"),
            "primitive_placement": placement(properties, "Placement"),
            "attachment_offset": placement(properties, "AttachmentOffset"),
        },
        "source_attachment_mode": 0,
        "source_payload_count_retained_in_plan": len(document.brep_payloads),
        "source_provenance_count_retained_in_plan": len(provenance),
    }


def verify_target(request, plan, data):
    from AuditFreecadBoxReleases import read_box
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    prior = request["intact"]["generated_projection"]
    measured = request["native"]["generated"]
    assert data == pinned(Path(request["candidate_path"]), measured["file_sha256"])
    assert prior["generated_sha256"] == measured["file_sha256"] and len(data) == prior["generated_bytes"]
    archive = SldprtArchive.from_bytes(data)
    streams = measured["exact_critical_streams"] | measured["exact_version_metadata"]
    assert sorted(streams) == prior["native_tested_streams"] and len(streams) == 10
    for name, row in streams.items():
        raw = archive.require(name)
        assert row["byte_identity"] and len(raw) == row["bytes"] and sha256(raw).hexdigest() == row["sha256"]
    target = open_document(data, source_format="solidworks.sldprt", strict=True)
    target.assert_valid()
    sketch, = target.sketches
    plane, = (row for row in target.support_planes if row.id == sketch.support_plane_id)
    body, = target.bodies
    solid, = target.brep.bodies
    boss, = (row for row in target.feature_timeline if row.id == body.final_feature_id)
    assert (plane.id, body.id, boss.id) == (prior["origin_sketch_plane_id"], prior["body_id"], prior["boss_id"])
    assert plane.name == "Front Plane" and frame(plane.transform) == IDENTITY
    assert solid.design_body_id == body.id and not boss.suppressed
    assert sum(row.format_id.startswith("freecad.fcstd") for row in target.brep_payloads) == prior["target_source_freecad_payloads"] == 0
    assert not target.materials and body.material_id is None
    tolerances = {name: sorted(set(row.tolerance for row in getattr(target.brep, name)), key=str)
                  for name in ("vertices", "edges", "faces")}
    assert tolerances == prior["target_geometry_tolerances_mm"]
    driver_by_name = {row.name: row for row in target.parameters}
    assert set(driver_by_name) == set(DIMENSIONS)
    bindings = {}
    for name, origin in zip(DIMENSIONS, plan.SourceDrivers, strict=True):
        row = driver_by_name[name]
        assert row.value == origin.value and row.role == origin.role
        bindings[name] = {"source_id": origin.id, "target_id": row.id, "target_owner_id": row.owner_id,
                          "native_name": plan.PartSource.ParameterBindings[origin.id], "millimeters": row.value.value}
    assert bindings == prior["live_driver_bindings"]
    assert set(sketch.parameter_ids) == {driver_by_name[name].id for name in DIMENSIONS[:2]}
    assert {row.parameter_id for row in sketch.constraints if row.kind == "distance"} == set(sketch.parameter_ids)
    assert boss.parameter_ids == (driver_by_name["Height"].id,) and boss.definition.length == driver_by_name["Height"].value
    partial = plan.PartSource
    expected = {"source_text": {"file": partial.PropertiesValue.DocumentFields, "summary": partial.PropertiesValue.SummaryFields},
                "source_body_label": partial.SourceBodyName, "source_dimensions_mm": partial.DimensionsValue}
    typed = read_box(data, expected, request["native"]["source_release"])
    assert typed == prior["typed_read"] == measured["normal_sdk_read"]
    assert sorted(expected["source_text"]["file"]) == prior["literal_text_property_names"]
    assert target.metadata["custom_properties"]["FreeCAD Uid"] == plan.SourceLineage.DocumentUuid
    assert [row.attributes["freecad_path"] for row in plan.SourceDrivers] == list(DIMENSIONS)
    return {
        "generated_sha256": measured["file_sha256"], "generated_bytes": len(data), "full_measured_candidate_byte_match": True,
        "exact_native_tested_streams": sorted(streams), "original_logical_destination": prior["original_logical_destination"],
        "creation_epoch": partial.CreationEpoch, "strict_native_part_readback": typed, "live_driver_bindings": bindings,
        "target_plane": {"id": plane.id, "label": plane.name, "frame": frame(plane.transform)},
        "target_body_id": body.id, "target_creator_id": boss.id, "target_geometry_tolerances_mm": tolerances,
        "target_source_freecad_payloads": 0, "source_analytic_geometry": dict(partial.GeometryValue),
    }


def verify_refusal(document, request):
    from VerifyFreecadF14aIntact import no_runtime_io
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import PlanOriginBox
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import ReadBoxSource

    with no_runtime_io():
        diagnostic = refused(PlanOriginBox, document, request["refusal"])
        result = {"refusal": diagnostic, "source_sha256": request["sha256"], "runtime_input_reads": 0}
        if "same_map" in request:
            sidecar, = next(row for row in document.brep_payloads if row.id == "freecad:brep:Body:Shape").attributes["freecad_sidecars"]
            assert sidecar["source_stream"] == "Body.Shape.Map.txt" and sha256(sidecar["data"]).hexdigest() == request["same_map"]
            attached = ReadBoxSource(document)
            assert attached.PropertiesValue.DocumentFields["FreeCAD Attachment Support Id"] == "freecad:plane:XZ_Plane"
            assert attached.GeometryValue["bounds_mm"] == [[0.0, -10.0, 0.0], [20.0, 0.0, 30.0]]
            result |= {"same_body_map_sha256_as_positive": request["same_map"], "still_admitted_by_attached_projector": True,
                       "attached_geometry": dict(attached.GeometryValue)}
    return result


def verify_request(request):
    sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent.parent)]
    from VerifyFreecadF14aIntact import no_runtime_io, normal_write_boundaries, wire
    from convert import open_document
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBoxPart
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import PlanOriginBox

    source = Path(request["path"])
    raw = pinned(source, request["sha256"])
    document = open_document(source, strict=True, include_brep=True, include_tessellation=True)
    document.assert_valid()
    assert document.source.sha256 == request["sha256"] and document.brep is not None
    for encoding in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(encoding)
    if "refusal" in request:
        return verify_refusal(document, request)
    before = document.to_dict()
    portable = type(document).from_json(document.to_json(indent=None))
    assert portable.to_dict() == before
    prior = request["intact"]
    path = prior["generated_projection"]["original_logical_destination"]
    sanitized = before | {"source": before["source"] | {"path": "<disclosed source>"}}
    assert sha256(wire(sanitized)).hexdigest() == prior["strict_source_model_sha256_without_locator"]
    with no_runtime_io():
        plan = PlanOriginBox(document)
        rebuilt = PlanOriginBox(portable)
        assert plan == rebuilt and plan.SourceDocument is document and rebuilt.SourceDocument is portable
        target = rebuilt.PartSource
        generated = MakeOriginBoxPart(target.ModelValue, path, target.CreationEpoch, target.PropertiesValue, UnitsValue=target.UnitsValue)
    ownership = verify_source(plan, request["lineage"], prior["retained_owners"])
    target_proof = verify_target(request, plan, generated.BytesValue)
    with TemporaryDirectory(prefix="kit-f14a-plan-refusal-") as output:
        boundary = normal_write_boundaries(document, source, Path(output) / "F14a.SLDPRT")
    assert boundary == {key: prior[key] for key in boundary}
    assert document.to_dict() == before and pinned(source, request["sha256"]) == raw
    return ownership | target_proof | boundary | {
        "source_model_unchanged": True, "json_rehydrated_plan_exact": True, "runtime_input_reads": 0,
        "prior_target_projection_receipt_sha256": sha256(wire(prior["generated_projection"])).hexdigest(),
    }


def capture(manifest, candidates):
    inputs = json.loads(pinned(manifest, MANIFEST))
    receipts = ROOT / "re/solidworks/measurements/2026"
    native = json.loads(pinned(receipts / "SdkFreecadBoxReleaseNative01.json", NATIVE))
    intact = json.loads(pinned(receipts / "SdkFreecadF14aIntactSource01.json", INTACT))
    lineage = json.loads(pinned(receipts / "SdkFreecadF14aTypedOwner01.json", LINEAGE))
    assert inputs["heldout_inputs"] == 0 and native["scoped_native_lifecycle_passed"] and not native["public_writer_qualified"]
    cases = {}
    workers = 0
    for name in (*POSITIVE, *NEGATIVE):
        entry, = (row for row in inputs["inputs"] if row["case"] == name)
        request = dict(entry)
        if name in POSITIVE:
            role = POSITIVE[name]
            case, = (row for row in native["cases"] if row["role"] == role)
            assert entry["sha256"] == case["source_freecad_sha256"] == lineage["cases"][name]["source_sha256"]
            request |= {"native": case, "intact": intact["cases"][name], "lineage": lineage["cases"][name],
                        "candidate_path": str(candidates / role / "F14a.SLDPRT")}
        else:
            digest, request["refusal"] = NEGATIVE[name]
            assert entry["sha256"] == digest
            if name == "recipe-1.0.2-F14c":
                request["same_map"] = lineage["cases"]["recipe-1.0.2-F14a"]["element_map_sha256"]
        outputs = []
        for _ in range(2 if name in POSITIVE else 1):
            result = run((sys.executable, "-I", "-B", __file__, "--worker"), input=json.dumps(request),
                         capture_output=True, text=True, timeout=90)
            if result.returncode or result.stderr:
                raise ValueError(f"{name}: SDK worker failed\n{result.stderr}")
            outputs.append(json.loads(result.stdout))
            workers += 1
        assert outputs == [outputs[0]] * len(outputs)
        cases[name] = outputs[0]
    purpose = ROOT / "src/convert/adapters/solidworks/Core/Preparation/FreecadBox"
    dependencies = [*sorted(purpose.rglob("*.py")), *sorted((ROOT / "src/convert/adapters/freecad/BodyLineage").glob("*.py")),
                    *sorted(Path(__file__).resolve().parent.glob("VerifySdkBoxLineage.py")),
                    *(ROOT / "re/tooling/sw2026" / name for name in ("VerifyFreecadF14aIntact.py", "AuditFreecadBoxReleases.py")),
                    Path(__file__).resolve()]
    return {
        "schema": "kit.sw2026.freecad-f14a-origin-planner.v1", "baseline_revision": BASELINE,
        "source_manifest_sha256": MANIFEST, "prior_native_release_receipt_sha256": NATIVE, "prior_intact_source_receipt_sha256": INTACT,
        "prior_typed_lineage_receipt_sha256": LINEAGE, "previously_measured_oracle_build": native["oracle_build"],
        "dependencies_sha256": {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in dependencies},
        "independent_sdk_processes": workers, "cases": cases, "new_native_processes": 0, "heldout_inputs_read": 0,
        "intact_source_transfer_qualified": False, "public_writer_qualified": False, "source_reference_transfer_qualified": False,
        "historical_corpus_conversions_counted": 0,
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(verify_request(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        parser = ArgumentParser(description="Audit the disclosed FreeCAD F14a typed origin planner")
        parser.add_argument("manifest", type=Path)
        parser.add_argument("native_candidates", type=Path)
        parser.add_argument("--output", required=True, type=Path)
        args = parser.parse_args()
        receipt = capture(args.manifest, args.native_candidates)
        data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as stream:
            stream.write(data)
        print(json.dumps({"receipt_sha256": sha256(data).hexdigest(), "independent_sdk_processes": receipt["independent_sdk_processes"]}))
