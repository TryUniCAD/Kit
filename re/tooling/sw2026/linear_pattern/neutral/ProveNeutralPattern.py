from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from subprocess import check_output, run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent),
                str(HERE.parents[2]), str(HERE.parents[2] / "serial")]

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.BoundPlaneValues import GetDatumFrame
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import LinearPattern
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource
from interchange.Records.RecordTopology import TopologyCounts
from interchange.serialization.EncodeData import ToData

from CheckPatternAngleOwners import require
from MakeLocalPatternDrivers import PatternDriverStyle
from NeutralPatternInput import (AngularLabelIntent, AnnotationViewIntent, NeutralPatternInput,
                                 PatternPresentation, PlaneIntersectionAxis)
from ProveLocalPatternContainer import COMPARISON_SCOPE, authored_layouts


EXPECTED = {
    "Packet/Packet.json": "da60bbfdc5411448b9aa5cd06c2a8772a0e0f2c39efa14ba2dc336c625e32cb1",
    "Packet/Build.json": "b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3",
    "NativeResult/Result.json": "ae4f5853e4066a0d3f00cf4cbdaac12797b18c55c268ada6431d7e062bd5d23b",
}
WRITER = "d644ff7beb6b61a147a3b5de82ba5614efb155c8"
COMPILER = HERE.parent.parent / "LocalPatternContainerProcess.py"
INPUT_FILES = (HERE, HERE.with_name("NeutralPatternInput.py"), HERE.with_name("ProjectNeutralPattern.py"),
               HERE.with_name("NeutralPatternProcess.py"))


def digest(data):
    return sha256(data).hexdigest()


def encode(data):
    return (json.dumps(data, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def plane(label, axis):
    base = PrincipalFrame(axis)
    origin, u, v, normal = (SpaceVector(*axis) for axis in (base.OriginValue, base.AxisU, base.AxisV, base.NormalValue))
    return SupportPlane("plane/" + axis, label, Transform(origin, u, v, normal))


def pick(key, name, kind, target, subelement=""):
    return Selection("pick/" + key, name, (SelectPathElem(kind, target, subelement),))


def profile(key, row, front):
    (a, b, _), (c, d, _) = row["bounds_m"]
    points = tuple(PlaneVector(x * 1000.0, y * 1000.0) for x, y in ((a, b), (c, b), (c, d), (a, d)))
    ids = tuple(f"{key}/edge/{index}" for index in range(4))
    edges = tuple(SketchEntity(label, GeometryKind.KLine, LineGeometry(start, end))
                  for label, start, end in zip(ids, points, (*points[1:], points[0]), strict=True))
    relations = tuple(SketchRelation(f"{key}/relation/{index}", "vertical" if index % 2 else "horizontal",
                                     (ConstraintRef(label),)) for index, label in enumerate(ids))
    return Sketch("sketch/" + key, row["sketch"], front.id, edges, relations, closed_profile_entity_ids=(ids,))


def depth_step(key, row, sketch, order, prior=(), selection=()):
    identity = "feature/" + key
    amount = ParameterValue(row["bounds_m"][1][2], ValueKind.KLength, "m")
    driver = Parameter("depth/" + key, "D1", amount, owner_id=identity)
    feature = FeatureStep(identity, row["feature"], FeatureKind.KExtrusion, order, prior, sketch.id, (driver.id,),
                          BooleanOp.KJoin if prior else BooleanOp.KCreate,
                          ExtrudeFeature(length=amount, direction=SpaceVector(0.0, 0.0, 1.0)), selection)
    return feature, driver


def author_document(authored):
    seed, plane_data, pattern_data = (authored[name] for name in ("seed", "plane", "pattern"))
    front, top, right = (plane(label, axis) for label, axis in
                         (("Front Plane", "z"), ("Top Plane", "y"), ("Right Plane", "x")))
    plate_sketch, seed_sketch = (profile(name, seed[name], front) for name in ("plate", "seed"))
    plate, plate_depth = depth_step("plate", seed["plate"], plate_sketch, 0)
    stock = pick("plate-stock", "Plate stock", "feature", plate.id, "body")
    boss, seed_depth = depth_step("seed", seed["seed"], seed_sketch, 1, (plate.id,), (stock.id,))
    hinge_top = pick("hinge-top", "First hinge plane", "support_plane", top.id)
    hinge_right = pick("hinge-right", "Second hinge plane", "support_plane", right.id)
    height_mm = seed["seed"]["bounds_m"][1][2] * 1000.0
    axis = FeatureStep("feature/axis", authored["axis"], FeatureKind.KReference, 2,
                       definition=PlaneIntersectionAxis(hinge_top.id, hinge_right.id,
                                                        SpaceVector(0.0, 0.0, height_mm * 1.05),
                                                        SpaceVector(0.0, 0.0, height_mm * -0.05)),
                       selection_ids=(hinge_top.id, hinge_right.id))
    angle_right = pick("angle-right", "Angled plane base", "support_plane", right.id)
    angle_axis = pick("angle-hinge", "Angled plane hinge", "feature", axis.id)
    angle_parameter = Parameter("parameter/angle", "D1", ParameterValue(plane_data["angle_rad"], ValueKind.KAngle, "rad"),
                                owner_id="feature/angle")
    zero = Parameter("parameter/offset", "Reference offset", ParameterValue(0.0, ValueKind.KLength, "mm"),
                     role=ParameterRole.KDerived, owner_id=angle_parameter.owner_id)
    angle_def = BoundDatum("plane/direction", angle_parameter.id, zero.id, "angle", right.transform)
    angle = FeatureStep(angle_parameter.owner_id, plane_data["name"], FeatureKind.KReference, 3, (axis.id,),
                        parameter_ids=(angle_parameter.id, zero.id), definition=angle_def,
                        selection_ids=(angle_right.id, angle_axis.id))
    angled = SupportPlane(angle_def.SupportPlaneId, angle.name,
                          GetDatumFrame(angle, angle_def, {value.id: value for value in (angle_parameter, zero)}),
                          angle_right.id, zero.id)
    direction = pick("direction", "Pattern direction", "support_plane", angled.id)
    selected = pick("seed-stock", "Joined seed stock", "feature", boss.id, "body")
    number = pattern_data["count"]
    count = Parameter("parameter/count", "D1", ParameterValue(number, ValueKind.KInteger), owner_id="feature/pattern")
    pitch = Parameter("parameter/pitch", "D3", ParameterValue(pattern_data["pitch_m"], ValueKind.KLength, "m"),
                      owner_id=count.owner_id)
    pattern = FeatureStep(count.owner_id, pattern_data["name"], FeatureKind.KPattern, 4, (boss.id, angle.id),
                          parameter_ids=(count.id, pitch.id), operation=BooleanOp.KJoin,
                          definition=LinearPattern(pitch.value, number, direction.id, pattern_data["reverse"]),
                          selection_ids=(direction.id, selected.id))
    summary = TopologyCounts(solid_count=1, shell_count=1, face_count=6 + 5 * number,
                             edge_count=12 + 12 * number, vertex_count=8 + 8 * number)
    document = CadDocument(
        CadSource("kit-neutral", "<independent oblique authored layout>", digest(encode(authored))),
        (Configuration("config/active", seed["configuration"], True),),
        (plate_depth, seed_depth, angle_parameter, zero, count, pitch), (front, top, right, angled),
        (plate_sketch, seed_sketch), (stock, hinge_top, hinge_right, angle_right, angle_axis, direction, selected),
        (plate, boss, axis, angle, pattern), (DesignBody("body/result", pattern.name, pattern.id, summary),),
        metadata={"name": seed["name"]}, units=UnitSystem.KMillimeter,
    )
    catalog = authored["annotation"]
    label = AngularLabelIntent(angle_parameter.id, plane_data["annotation_view"], plane_data["design_intent"],
                               plane_data["selected_leader"], tuple(plane_data["shifted_point_m"]))
    visual = PatternPresentation(
        label, count.id, pitch.id,
        tuple(PatternDriverStyle(**{**row, "label_m": tuple(row["label_m"])}) for row in pattern_data["styles"]),
        tuple(AnnotationViewIntent(view["name"], tuple(map(tuple, view["basis"]))) for view in catalog["views"]),
        catalog["active"], tuple(catalog["shown"]),
    )
    return NeutralPatternInput(document, SelfFileInput(seed["path"], seed["epoch"]), visual)


def guarded(model, *flags):
    command = (sys.executable, "-I", "-B", str(HERE.with_name("NeutralPatternProcess.py")), *flags)
    payload = encode(ToData(model))
    return payload, run(command, input=payload, cwd=ROOT, capture_output=True, timeout=45, check=False)


def read_if_passed(observation):
    require(observation.returncode == 0 and not observation.stderr,
            "guarded neutral pattern failed\n" + observation.stderr.decode())
    return json.loads(observation.stdout)


def checked_file(root, name, pin):
    path = root / name
    require(path.is_file() and path.resolve().is_relative_to(root) and not path.is_symlink(),
            "disclosed evidence path escaped its original packet")
    raw = path.read_bytes()
    require(digest(raw) == pin, "disclosed evidence file digest differs")
    return raw


def validated_disclosed(root):
    require(root.name == "GeneratedLocalPatternNative02", "use only the corrected disclosed candidate packet")
    packet, build, result = (json.loads(checked_file(root, name, sha)) for name, sha in EXPECTED.items())
    require(packet["native_build"] == result["build"] == "34.5.2.0604"
            and result["packet_sha256"] == EXPECTED["Packet/Packet.json"]
            and result["build_sha256"] == EXPECTED["Packet/Build.json"]
            and result["passed"] and result["heldout_cases"] == 0 and result["distinct_processes"] == 6
            and len(result["phases"]) == 4 and all(row["passed"] for row in result["phases"].values())
            and len(result["controls"]) == 2 and all(row["passed"] for row in result["controls"].values()),
            "corrected candidate provenance is not the controlled disclosed comparison")
    return packet, build["model_cases"]


def compare_modes(authored, record):
    model = author_document(authored)
    wire, measured = guarded(model)
    actual = read_if_passed(measured)
    require(actual["neutral_wire_roundtrip"] and actual["guarded_runtime_reads"] == actual["application_modules_loaded"] == 0
            and actual["neutral_owner_counts"] == {
                "bodies": 1, "feature_timeline": 5, "parameters": 6, "selections": 7, "sketches": 2, "support_planes": 4,
            } and actual["typed_replay_count"] == 9
            and actual["native_container"] == record["native_container"]
            and actual["observed"] == record["observed"] and actual["streams"] == record["streams"]
            and actual["map_counters"] == record["map_counters"] and actual["analytic_geometry"] == record["analytic_geometry"]
            and json.loads(encode(authored)) == actual["modeled_input"] == record["modeled_input"],
            "validated neutral model did not reproduce the exact disclosed typed graph")
    return model, {"neutral_wire_sha256": digest(wire), **{key: value for key, value in actual.items()
                                                           if key != "modeled_input"}}


def change_step(model, index, **changes):
    document = model.document
    steps = list(document.feature_timeline)
    steps[index] = replace(steps[index], **changes)
    return replace(model, document=replace(document, feature_timeline=tuple(steps)))


def negative_models(model):
    document = model.document
    plate, seed, axis, angle, pattern = document.feature_timeline
    picks = document.selections
    params = document.parameters
    body, = document.bodies
    sketch, seed_sketch = document.sketches
    front, top, right, oblique = document.support_planes
    displaced = replace(oblique.transform, origin=SpaceVector(0.01, 0.0, 0.0))
    wrong_count = replace(params[-2], value=ParameterValue(5, ValueKind.KInteger))
    wrong_pick = replace(picks[-1], path=(SelectPathElem("feature", plate.id, "body"),))
    yield "missing_typed_hinge", change_step(model, 2, definition=None), "typed finite plane-intersection axis is required"
    yield "crossed_hinge_slots", change_step(model, 2, selection_ids=axis.selection_ids[::-1]), "two ordered support selections"
    yield "contradicted_trim", change_step(model, 2, definition=replace(axis.definition, end_mm=SpaceVector(0.0, 0.0, -2.0))), "directed first-plane trim"
    yield "missing_closed_loop", replace(model, document=replace(document, sketches=(replace(sketch, closed_profile_entity_ids=()), seed_sketch))), "closed line loop"
    yield "nonlocal_seed_scope", replace(model, document=replace(document, selections=(*picks[:-1], wrong_pick))), "exact local body owner"
    yield "count_driver_conflicts", replace(model, document=replace(document, parameters=(*params[:-2], wrong_count, params[-1]))), "D1/D3 drivers disagree"
    yield "angle_frame_conflicts", replace(model, document=replace(document, support_planes=(front, top, right, replace(oblique, transform=displaced)))), "controls disagree with its support frame"
    yield "crossed_angle_pitch_view", replace(model, presentation=replace(model.presentation, count_parameter_id=params[-1].id)), "presentation is not bound"
    yield "false_body_result", replace(model, document=replace(document, bodies=(replace(body, final_feature_id=seed.id),))), "final neutral body contradicts"
    yield "metadata_cannot_supply_hinge", replace(model, document=replace(document, metadata={**document.metadata, "hinge": "Top+Right"})), "ordinary neutral part name"
    yield "unowned_native_depth", replace(model, document=replace(document, parameters=(replace(params[0], owner_id=seed.id), *params[1:]))), "actual unexpressed driving parameters"


def verify_refusals(model):
    results = {}
    _, ordinary = guarded(model, "--without-axis-type")
    require(ordinary.returncode != 0 and not ordinary.stdout and b"unknown data type 'PlaneIntersectionAxis'" in ordinary.stderr,
            "plain type registry unexpectedly reconstructed the finite axis")
    results["unregistered_finite_axis"] = "unknown data type 'PlaneIntersectionAxis'"
    for name, changed, reason in negative_models(model):
        _, refused = guarded(changed)
        require(refused.returncode != 0 and not refused.stdout and reason in refused.stderr.decode(),
                "neutral contrast did not refuse at its intended ownership boundary " + name + "\n" + refused.stderr.decode())
        results[name] = reason
    return results


def git(*args):
    return check_output(("git", *args), cwd=ROOT).decode().strip()


def pinned_code():
    tree = git("rev-parse", WRITER + ":src")
    require(git("rev-parse", "HEAD:src") == tree
            and not git("diff", "--name-only", WRITER, "--", "src", "re/tooling/sw2026",
                        "tests/Convert/Solidworks/Research/ConstructionGuard.py",
                        ":(exclude)re/tooling/sw2026/linear_pattern/evaluation",
                        ":(exclude)re/tooling/sw2026/linear_pattern/neutral"),
            "neutral proof needs the exact unchanged corrected SDK, compiler and process guard")
    return tree


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "choose a fresh neutral pattern receipt")
    source_tree = pinned_code()
    root = args.disclosed.resolve()
    packet, old = validated_disclosed(root)
    reports, contrasts = {}, {}
    for authored, alternate_pitch in authored_layouts():
        name = authored["seed"]["name"]
        cases = {
            "original": authored,
            "pitch_only": {**authored, "pattern": {**authored["pattern"], "pitch_m": alternate_pitch}},
            "count_only": {**authored, "pattern": {**authored["pattern"], "count": authored["pattern"]["count"] + 1}},
        }
        reports[name] = {}
        for role, request in cases.items():
            neutral, report = compare_modes(request, old[name][role])
            reports[name][role] = report
            if role == "original":
                initial = report
                _, transport = guarded(neutral, "--binary")
                prior = checked_file(root, "Packet/" + name + ".SLDPRT", packet["files"][name + ".SLDPRT"])
                require(transport.returncode == 0 and not transport.stderr and transport.stdout == prior,
                        "modeled neutral candidate binary differs from the corrected disclosed container")
                report["byte_equal_to_disclosed"] = True
                if not contrasts:
                    contrasts = verify_refusals(neutral)
            else:
                changed = tuple(sorted(stream for stream in initial["streams"]
                                       if initial["streams"][stream] != report["streams"][stream]))
                require(changed == COMPARISON_SCOPE, "neutral driver edit changed unrelated native owners")
                report["changed_streams"] = changed
    require(pinned_code() == source_tree, "frozen compiler changed during the guarded proof")
    receipt = {
        "schema": "kit.sw2026.oblique-linear-pattern-neutral-input.v1", "native_build": "34.5.2.0604",
        "writer_revision": WRITER, "writer_source_tree": source_tree,
        "source_evidence": EXPECTED, "cases": reports, "refused_neutral_contrasts": contrasts,
        "guarded_processes": 8 + len(contrasts), "no_new_oracle_execution": True,
        "native_holdout_credit": 0, "registered_public_writer": False,
        "tools": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in (*INPUT_FILES, COMPILER)},
    }
    with args.output.open("xb") as output:
        output.write(encode(receipt))
    print(json.dumps({"sha256": digest(args.output.read_bytes()), "exact_disclosed_binaries": len(reports),
                      "neutral_refusals": len(contrasts), "guarded_processes": receipt["guarded_processes"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
