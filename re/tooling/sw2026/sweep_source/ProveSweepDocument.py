from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from math import pi
from pathlib import Path
from subprocess import check_output
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE)]
from ProveSdkSweepPart import (
    BuildSweepPart, MEASURED, NATIVE, SPEC, checked_json, expected_refusal,
    guard_runtime, inspect_output, make_intent,
)
from SweepModel import PATH, SECTION, SWEEP, dimensions, require, validate_spec
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Core.Preparation.Sweeps.PlanSweepPart import PlanSweepPart
from interchange import SweepFeature
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.materials.MaterialRecord import MaterialRecord
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource
from interchange.serialization.JsonCodec import DumpJson, LoadJson


def neutral_support(identifier, name, axis):
    frame = PrincipalFrame(axis)
    return SupportPlane(identifier, name, Transform(
        *(SpaceVector(*vector) for vector in (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue))
    ))


def neutral_section(radius_mm):
    entity = SketchEntity("section-circle", GeometryKind.KCircle, CircleGeometry(PlaneVector(0.0, 0.0), radius_mm))
    center = ConstraintRef(entity.id, "center")
    diameter = Parameter("circle-diameter", "D1", ParameterValue(radius_mm * 2, ValueKind.KLength, "mm"), owner_id="section-sketch")
    rows = (SketchRelation("section-origin", "fixed", (center,)),
            SketchRelation("section-diameter", "diameter", (ConstraintRef(entity.id),), diameter.id))
    sketch = Sketch("section-sketch", SECTION, "right", (entity,), rows, (diameter.id,), ((entity.id,),))
    return sketch, diameter


def neutral_path(radius_mm):
    entity = SketchEntity("path-arc", GeometryKind.KArcGeometry,
                         ArcGeometry(PlaneVector(0.0, radius_mm), radius_mm, -pi / 2, 0.0))
    center, start, end = (ConstraintRef(entity.id, point) for point in ("center", "start", "end"))
    radius = Parameter("arc-radius", "D1", ParameterValue(radius_mm, ValueKind.KLength, "mm"), owner_id="path-sketch")
    rows = (
        SketchRelation("path-origin", "fixed", (start,)),
        SketchRelation("path-vertical", "vertical", (center, start)),
        SketchRelation("path-horizontal", "horizontal", (end, center)),
        SketchRelation("path-radius", "radius", (ConstraintRef(entity.id),), radius.id),
    )
    return Sketch("path-sketch", PATH, "front", (entity,), rows, (radius.id,)), radius


def neutral_document(name, section_radius, path_radius, density):
    section, diameter = neutral_section(section_radius * 1000.0)
    path, radius = neutral_path(path_radius * 1000.0)
    step = FeatureStep("sweep-boss", SWEEP, FeatureKind.KSweep, 1, sketch_id=section.id,
                       operation=BooleanOp.KCreate, definition=SweepFeature(path.id))
    body = DesignBody("swept-solid", SWEEP, step.id)
    physical = Parameter("body-density", "Density", ParameterValue(density, ValueKind.KQuantity, "kg/m3"), owner_id=body.id)
    return CadDocument(CadSource("neutral", "", ""), (Configuration("default", "Default", True),),
                       (diameter, radius, physical),
                       (neutral_support("front", "Front Plane", "z"), neutral_support("right", "Right Plane", "x"),
                        neutral_support("top", "Top Plane", "y")),
                       (section, path), (), (step,), (body,), metadata={"name": name})


def check_refusals(document, target):
    step, = document.feature_timeline
    section, path = document.sketches
    diameter, radius, physical = document.parameters
    missing_path = replace(document, feature_timeline=(replace(step, definition=SweepFeature("absent-sketch")),))
    alias = replace(document, feature_timeline=(replace(step, definition=SweepFeature(section.id)),))
    wrong_kind = replace(document, feature_timeline=(replace(step, kind=FeatureKind.KRevolution),))
    wrong_owner = replace(document, parameters=(diameter, replace(radius, owner_id=section.id), physical))
    wrong_density = replace(document, parameters=(diameter, radius, replace(physical, owner_id=path.id)))
    wrong_path = replace(document, sketches=(section, replace(path, support_plane_id=section.support_plane_id)))
    detached = replace(document, sketches=(section, replace(path, constraints=path.constraints[:-1])))
    dimension = replace(diameter.value, value=diameter.value.value + 0.001)
    stale_cache = replace(document, parameters=(replace(diameter, value=dimension), radius, physical))
    opaque = replace(document, metadata=dict(document.metadata) | {"presentation": "unprojected"})
    assigned = replace(document, materials=(MaterialRecord("material", "Named aluminium", 2700.0, (1.0, 0.0, 0.0, 1.0)),),
                       bodies=(replace(document.bodies[0], material_id="material"),))
    refused = (
        (missing_path, "distinct actual path sketch"),
        (alias, "distinct actual path sketch"),
        (wrong_kind, "sweep definition on non-sweep feature"),
        (wrong_owner, "actual unexpressed driving parameters"),
        (wrong_density, "actual unexpressed driving parameters"),
        (wrong_path, "exact Right section and Front path supports"),
        (detached, "actual D1 radius"),
        (stale_cache, "diameter driver disagrees"),
        (opaque, "editable geometry only"),
        (assigned, "editable geometry only"),
    )
    notes = [expected_refusal(lambda: PlanSweepPart(doc, target), diagnostic) for doc, diagnostic in refused]
    untyped = replace(document, feature_timeline=(replace(step, definition=None),))
    AssertValid(untyped)
    notes.append(expected_refusal(lambda: PlanSweepPart(untyped, target), "active typed first creator"))
    return notes


def worker(case, density, mode):
    radii = dimensions(case, None if mode == "original" else mode)
    blocked = guard_runtime()
    document = neutral_document(case["name"], *radii, density)
    authored = make_intent(case["name"], *radii, density)
    text = DumpJson(document)
    decoded = LoadJson(text)
    require(type(decoded) is CadDocument and DumpJson(decoded) == text, "typed sweep did not survive neutral JSON exactly")
    require(decoded.feature_timeline[0].definition.PathSketchId == decoded.sketches[1].id
            and decoded.feature_timeline[0].sketch_id == decoded.sketches[0].id,
            "neutral wire lost the independent resolved sketch links")
    intent = PlanSweepPart(decoded, authored.OutputValue)
    require(intent == authored, "neutral sketch and density owners did not project the frozen sweep intent")
    reordered = replace(decoded, sketches=tuple(reversed(decoded.sketches)), parameters=tuple(reversed(decoded.parameters)),
                        support_planes=tuple(reversed(decoded.support_planes)))
    require(PlanSweepPart(reordered, authored.OutputValue) == intent, "planner used inventory order instead of actual identities")
    candidate = BuildSweepPart(intent)
    require(candidate.BytesValue == BuildSweepPart(authored).BytesValue, "portable route differs from direct typed intent")
    proof = inspect_output(candidate.BytesValue, candidate.StreamsValue, candidate.ConfigValue, candidate.ResolvedValue, radii)
    notes = check_refusals(decoded, authored.OutputValue)
    require(not blocked, "neutral sweep attempted unapproved runtime access")
    return {
        "candidate_sha256": proof["candidate_sha256"],
        "stream_sha256": proof["stream_sha256"],
        "json_sha256": sha256(text.encode()).hexdigest(),
        "name": case["name"], "state": mode, "target": authored.OutputValue.PathName,
        "driver_owners": [[row["name"], row["id"], row["dimension_id"], row["value_metres"]] for row in proof["sketches"]],
        "comparison_streams": proof["exact_stream_replays"],
        "map_counts": proof["map_counts"],
        "refusals": notes, "runtime_calls": len(blocked),
    }


def prove():
    density, cases = validate_spec(checked_json(HERE / "DisclosedSweepInputs.json", SPEC))
    native = checked_json(MEASURED, NATIVE)
    rows = []
    for case, witnessed in zip(cases, native["cases"], strict=True):
        states = []
        for mode in ("original", "section", "path"):
            data = json.dumps({"case": case, "density": density, "mode": mode}).encode()
            result = json.loads(check_output((sys.executable, "-I", "-B", str(__file__), "--worker"), input=data))
            states.append(result)
        original, section, path = states
        require(witnessed["passed"] and original["candidate_sha256"] == witnessed["candidate_sha256"]["original"]
                and original["driver_owners"][0] == path["driver_owners"][0]
                and original["driver_owners"][1] == section["driver_owners"][1],
                "neutral route changed witnessed native bytes or the other independent driver's ownership")
        rows.extend(states)
    prefix = ROOT / "src"
    sources = tuple((prefix / "convert/adapters/solidworks/Core/Preparation/Sweeps").glob("*.py"))
    sources += tuple(prefix / name for name in (
        "interchange/__init__.py", "interchange/history/__init__.py",
        "interchange/Features/SweepFeature.py", "interchange/document/Validation/SweepValidate.py",
        "interchange/document/Validation/StepLinkValidate.py",
    ))
    return {
        "schema": "kit.sw2026.portable-standard-sweep-typed.v1",
        "composer_revision": "81651174d675cb63e7debd90b1ccc91d97a5eb56",
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in sorted(sources)},
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "disclosed_intents_sha256": SPEC, "disclosed_native_result_sha256": NATIVE,
        "tested_cases": rows, "fresh_workers": len(rows),
        "native_processes_started": 0, "private_inputs_read": 0, "public_registration": False,
    }


def main():
    parser = ArgumentParser(description="prove portable Standard sweep identities and native-tested archive parity")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    result = worker(**json.load(sys.stdin)) if args.worker else prove()
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
