import argparse
from dataclasses import replace
from hashlib import sha256
from math import fsum, pi
from pathlib import Path
import codecs
import json
import subprocess
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from CheckConcentricSourceBrep import map_source_endpoints, read_cylinder_roles
from ConcentricNativeContract import ORACLE, ROLES, checked, close_numbers, digest, require, validate_prediction, write_json
from ConcentricNeutralAdmission import bind_cylinder, project_concentric
from PrepareGeneratedConcentric import generated_prediction, input_row, windows_path
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import ReadOccName
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylChild import ReadCylChild
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from para.concentric.ConcentricAssembly import principal_planes
from para.concentric.PrepareConcentricPersistence import OBSERVER, SCHEMA, derive_session
from para.concentric.ProjectConcentricRadialIntent import attach_scene, light_values, read_intents, source_scene
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, source_case
from para.concentric.ProveSignedConcentricWriter import emit_parts, inventory_receipt, neutral_d01, source_inventory, verify_parts
from para.cylinder.CylinderAttachment import attach_cylinder_mut


REVISION = "7e4f6e8d22f3181590e0ab238c0e0a6f4c756d02"
SIGNED_OFFLINE = "432e5cf3f8c67b88935ea8d44c0649ece62af5744b6b68faed1e54df8e47d3c6"
OLD_TRIAL = "5d7680db342c5c7e037313d0a2bc3e02820b1d21dfcbdad5cd77293430d32d01"
OLD_RESULT = "3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03"
FIXTURES = {
    "Aligned": ("ConcentricFeatureNeutral01.json", "e5e005dc738ad379f0485accc78d7f72002cccdc1b14186ea43ed82e4f444fe3"),
    "AntiLocked": ("ConcentricBrepNeutral01.json", "2b00d988374d26b39d6edfd2752fe488d7ad9a527a3d1913bdd384ee614fbf63"),
}


def neutral_contrast(document):
    graph = document.assembly
    root = "SignedTiltedLock"
    child = "SignedTiltedChild"
    definitions = tuple(replace(row, name=root if row.id == graph.root_definition_id else child) for row in graph.definitions)
    instances = tuple(replace(row, name=f"{child}-{ReadOccName(row.name)[1]}") for row in graph.instances)
    link, = graph.documents
    document = replace(document, metadata={"name": root}, assembly=replace(
        graph, definitions=definitions, instances=instances,
        documents=(replace(link, document=replace(link.document, metadata={"name": child})),)))
    document.AssertValid()
    return document


def independent_protocol(document, edited_depth):
    graph = document.assembly
    child = graph.documents[0].document
    circle = child.sketches[0].entities[0].geometry
    radius, depth = circle.radius / 1000, child.feature_timeline[0].definition.length.value / 1000
    x, y = circle.center.x / 1000, circle.center.y / 1000
    instances = sorted(graph.instances, key=lambda row: row.order)
    transforms = [row.transform.values for row in instances]

    def shape(length):
        volume, area = pi * radius ** 2 * length, 2 * pi * radius * (radius + length)
        local = (x, y, length / 2)
        centers = [tuple(fsum(matrix[row * 4 + column] * local[column] for column in range(3))
                         + matrix[row * 4 + 3] / 1000 for row in range(3)) for matrix in transforms]
        mean = tuple((left + right) / 2 for left, right in zip(*centers, strict=True))
        return {
            "child": {"bodies": 1, "volume_m3": volume, "area_m2": area, "center_m": local},
            "assembly": {"bodies": 2, "volume_m3": 2 * volume, "area_m2": 2 * area, "center_m": mean},
        }

    names = {row.id: row.name for row in instances}
    entities = {row.id: row for row in graph.mate_entities}
    mate, = graph.mates
    return {
        "expected_readback": {"occurrence_order": [names[entities[identity].instance_path[0]] for identity in mate.entity_ids],
                              "fixed_flags": [row.fixed for row in instances], "mate_name": mate.name,
                              "com_mate_alignment": 0 if str(mate.alignment) == "aligned" else 1,
                              "rotation_locked": mate.attributes["rotation_locked"], "depth_m": depth,
                              "radius_m": radius, "expected_geometry": shape(depth)},
        "depth_edit": {"target_m": edited_depth, "expected_geometry": shape(edited_depth)},
    }


def signed_expectation(prediction, local_axes):
    ordered = [prediction["occurrences"][index] for index in prediction["endpoint_indexes"]]
    world_axes = [tuple(fsum(matrix["transform"][axis * 3 + coordinate] * vector[axis] for axis in range(3))
                        for coordinate in range(3)) for matrix, vector in zip(ordered, local_axes, strict=True)]
    return {
        "names": [row["name"] for row in ordered], "local_axes": local_axes, "world_axes": world_axes,
        "initial_bounds_m": [(0.0, prediction["depth_m"] * axis[2]) for axis in local_axes],
        "saved_bounds_by_carrier_sign_m": {
            str(sign): [(0.0, sign * prediction["edited_depth_m"] * axis[2]) for axis in local_axes]
            for sign in (1, -1)
        },
    }


def model_with_lights(document, scene, lights, destination, written_at):
    model = ReadAsmModel(document)
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, destination, written_at)
    child = model.ChildDocument
    plain = replace(child, brep=None)
    plan = ProjectCircle(plain)
    basic = MakePartRecipe(plan, written_at)
    folders = tuple((kind, scene if kind == "moEnvFolder_c" else label) for kind, label in basic.SystemValue.FolderValues)
    recipe = replace(basic, SystemValue=replace(basic.SystemValue, FolderValues=folders))
    setting = BindPartIntent(plain, plan, recipe, SelfFileInput(paths.ChildValue.PathName, written_at))
    session, updates = derive_session(plain, written_at)
    driver = "diameter" if plan.IsDiameter else "radius"
    attachment = attach_cylinder_mut(MakeCirclePart(plain, setting), session, updates, 0,
                                     tessellated_faces=True, driver_mode=driver)
    part = attach_scene(attachment.candidate, lights, setting.TargetValue)
    attachment = replace(attachment, candidate=part)
    nodes = {row.index: XmtNode(row.index, row.kind, row.fields) for row in attachment.projection.partition.nodes}
    profile = "derived_feature" if child.brep is None else "authored_brep"
    bound = bind_cylinder(child, part, nodes, profile=profile, driver_mode=driver)
    intent = project_concentric(document, {model.ChildValue.id: bound})
    metadata = MakeAsmRecipe(model, recipe, principal_planes(document, written_at), paths.ParentValue)
    placements = tuple(ReadAsmPlace(row) for row in model.Occurrences)
    return (attachment, intent, metadata, placements), paths


def build(document, axes, scene, intents, destination, written_at, expected):
    GetDocumentCaps(ReadAsmModel(document).ChildDocument)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    lights = read_intents(intents, written_at)
    active = True
    attempted = []

    def guard(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect"}:
            attempted.append(event)
            raise RuntimeError("signed packet construction attempted runtime access: " + event)

    sys.addaudithook(guard)
    try:
        bundle, paths = model_with_lights(document, scene, lights, destination, written_at)
        parent = emit_parts(bundle, axes)
        child = bundle[0].file_bytes
        repeated, _ = model_with_lights(document, scene, lights, destination, written_at)
        require(emit_parts(repeated, axes) == parent and repeated[0].file_bytes == child, "fresh signed writes differ")
        measurement = verify_parts(parent, bundle, axes)
        signed_rows(measurement["world_axes"], expected["world_axes"], "generated archive signed world axes")
        signed_rows(measurement["active_intervals"], expected["initial_bounds_m"], "generated archive signed intervals")
        archive = SldprtArchive.from_bytes(child)
        actual_scene, actual_lights = source_scene(ReadNativeLink(archive, 0))
        require((actual_scene, actual_lights) == (scene, lights), "generated child omitted its own complete lighting graph")
    finally:
        active = False
    require(not attempted, "runtime input accesses occurred")
    measurement.update(runtime_io_attempts=len(attempted), independent_builds=2,
                       ordered_child_lights=[row.NameValue for row in lights],
                       resolved_child_self_path=paths.ChildValue.PathName)
    return {"parent": parent, "child": child}, measurement


def signed_rows(actual, expected, label):
    require(len(actual) == len(expected) and all(close_numbers(left, right, relative=1e-10, absolute=1e-12)
                                               for left, right in zip(actual, expected, strict=True)), label + " differ")


def check_live_signs(result, expected, expected_control):
    live = {
        "ControlBefore": ("initial", "rebuilt"), "Generated": ("initial", "rebuilt", "edited", "saved_state"),
        "Reopen": ("initial", "rebuilt"), "ControlAfter": ("initial", "rebuilt"),
    }
    require(result["passed"] is True and result["controls_healthy"] is True and result["distinct_native_processes"] == 4
            and result["heldout_acceptance"] is False, "native lifecycle or bracket controls did not pass")
    checks = 0
    for role, keys in live.items():
        row = result["phases"][role]
        require(row["passed"] is True and row["open_errors"] == row["open_warnings"] == 0
                and row["immutable_inputs_unchanged"] is True
                and row["parameter_edits"] == int(role == "Generated") and row["file_saves"] == (2 if role == "Generated" else 0),
                "native phase lost zero diagnostics, immutable sources or its exact edit/save policy")
        target = expected_control if role.startswith("Control") else expected
        for key in keys:
            state = row[key]
            require(state["diagnostic_counts"] == {"child": 0, "assembly": 0}, "native state returned diagnostics")
            rows = state["mate"]["ordered_endpoints"]
            require([value["occurrence"] for value in rows] == target["names"], "live ordered occurrence owners differ")
            signed_rows([value["axis"] for value in rows], target["world_axes"], "live signed world axes")
            checks += len(rows)
    return checks


def check_saved(parent_path, child_path, hashes, expected, prediction):
    parent_bytes = checked(parent_path, hashes["parent"]).read_bytes()
    checked(child_path, hashes["child"])
    parent = open_document(parent_path, strict=True, include_brep=True, include_tessellation=False)
    child = parent.assembly.documents[0].document
    require(parent.source.sha256 == hashes["parent"] and child.source.sha256 == hashes["child"],
            "lost the exact owned native saved parent or child")
    owner = ReadCylChild(child_path, child, prediction["child_configuration"])
    shape = read_cylinder_roles(child, owner)
    require(close_numbers([shape.radius / 1000, (shape.centers[1][2] - shape.centers[0][2]) / 1000],
                          [prediction["radius_m"], prediction["edited_depth_m"]], relative=1e-12),
            "saved physical rim radius or depth differs")
    graph = parent.assembly
    instances = {row.id: row for row in graph.instances}
    mate, = graph.mates
    require(str(mate.alignment) == ("aligned" if prediction["api_alignment"] == 0 else "anti_aligned")
            and mate.attributes["rotation_locked"] is prediction["rotation_locked"],
            "saved mate lost its actual alignment or rotation lock")
    rows = map_source_endpoints(parent, parent_bytes, shape, shape)
    require([instances[row["occurrence"]].name for row in rows] == expected["names"], "saved ordered occurrences differ")
    signed_rows([value["local_axis"] for value in rows], expected["local_axes"], "saved signed local f108")
    signed_rows([value["world_axis"] for value in rows], expected["world_axes"], "saved signed world fe8")
    signed_rows([value["source_axial_bounds_m"] for value in rows],
                expected["saved_bounds_by_carrier_sign_m"][str(shape.carrier_sign)], "saved signed physical rim extents")
    return {"carrier_sign": shape.carrier_sign, "saved_real_face": shape.side_face, "endpoints": rows}


def host_verify(root, packet_sha):
    process = subprocess.run([sys.executable, "-B", str(root / "Tools" / OBSERVER),
                              "verify", str(root / "Trial.json"), packet_sha],
                             capture_output=True, text=True, check=True, timeout=40)
    require(json.loads(process.stdout)["passed"] is True, "the existing observer declined the frozen packet")


def stage_case(out, baseline_root, baseline, runtime, controls, source_closure, document, axes, scene, lights,
               prediction, signed, signed_control, written_at, case):
    names = {"parent": document.metadata["name"] + ".SLDASM",
             "child": document.assembly.documents[0].document.metadata["name"] + ".SLDPRT"}
    require(not out.exists(), "new owned packet directory required")
    target = windows_path(out / "Working" / names["parent"])
    files, proof = build(document, axes, scene, lights, target, written_at, signed)
    for label in ("Tools", "Evidence", "Frozen", "Working"):
        (out / label).mkdir(parents=True)
    for relative, wanted in baseline["files_sha256"].items():
        if relative.startswith("Tools/"):
            (out / relative).write_bytes(checked(baseline_root / relative, wanted).read_bytes())
    (out / "Evidence/GuestPython.json").write_bytes(runtime)
    write_json(out / "Evidence/Prediction.json", {"generated": prediction["generated"], "control": prediction["control"]})
    write_json(out / "Evidence/ExpectedSigned.json", {"generated": signed, "control": signed_control})
    write_json(out / "Evidence/Neutral.json", {"document": ToData(document), "local_axes": axes, "lights": lights})
    write_json(out / "Evidence/Build.json", proof)
    for directory in ("Frozen", "Working"):
        for role, payload in files.items():
            (out / directory / names[role]).write_bytes(payload)
    job = {
        "schema": SCHEMA, "roles": list(ROLES), "oracle_sha256": ORACLE, "require_preference_18_true": True,
        "heldout_inputs_read": 0, "native_processes_started": 0, "writer_revision": REVISION,
        "preparer_sha256": digest(Path(__file__)), "source_closure": source_closure, "case": case,
        "controls": controls, "working_names": names,
        "generated_sha256": {role: sha256(payload).hexdigest() for role, payload in files.items()},
        "files_sha256": {str(path.relative_to(out)): digest(path) for owner in ("Tools", "Evidence") for path in (out / owner).iterdir()},
    }
    trial = out / "Trial.json"
    write_json(trial, job)
    trial_sha = digest(trial)
    prefix = [json.loads(runtime)["executable"], "-B", windows_path(out / "Tools" / OBSERVER)]
    argument = windows_path(trial)
    argv = {"verify_guest": [*prefix, "verify", argument, trial_sha],
            **{role: [*prefix, "phase", argument, trial_sha, role] for role in ROLES},
            "summary": [*prefix, "summary", argument, trial_sha]}
    recipe = out / "Recipe.json"
    write_json(recipe, {"ordered_phases": list(ROLES), "always_run_trailing_control": True,
                        "argv": argv, "host_postflight_subcommand": ["postflight", str(trial), trial_sha]})
    host_verify(out, trial_sha)
    return {"trial_sha256": trial_sha, "recipe_sha256": digest(recipe), "files": job["generated_sha256"],
            "host_verify_passed": True, "expected": signed, "build": proof}


def prepare(base, out, written_at):
    baseline_root = base.resolve()
    require(not out.exists(), "use a new private signed discriminator directory")
    previous = json.loads(checked(baseline_root / "Trial.json", OLD_TRIAL).read_bytes())
    old = json.loads(checked(baseline_root / "Result.json", OLD_RESULT).read_bytes())
    require(old["packet_sha256"] == OLD_TRIAL and old["passed"], "existing radial controls and lifecycle are required")
    old_prediction = json.loads(checked(baseline_root / "Evidence/Prediction.json",
                                       previous["files_sha256"]["Evidence/Prediction.json"]).read_bytes())
    control_prediction = old_prediction["control"]
    runtime = checked(baseline_root / "Evidence/GuestPython.json", previous["files_sha256"]["Evidence/GuestPython.json"]).read_bytes()
    controls = {role: input_row(Path(prior["host_path"]), prior["sha256"]) for role, prior in previous["controls"].items()}
    require(controls == previous["controls"], "disclosed control locators changed")
    shapes = checked(REPO / "re/solidworks/measurements/2026/ConcentricSignedWrapperConstruction01.json", SIGNED_OFFLINE)
    signed_proof = json.loads(shapes.read_bytes())
    require(signed_proof["passed"] and all(
        digest(Path(__file__).with_name(name)) == checksum for name, checksum in signed_proof["source_tool_sha256"].items()
    ), "the exact proven signed writer and observer modules are required")
    source_closure = inventory_receipt(source_inventory(REPO))
    source_dir = Path(controls["parent"]["host_path"]).parent
    require(source_dir == Path(controls["child"]["host_path"]).parent, "controls must share their actual source directory")
    parent, original, shape = source_case(source_dir, Path(controls["parent"]["host_path"]).name,
                                          Path(controls["child"]["host_path"]).name, D01_LOCKED["Source"])
    source_axes = map_source_endpoints(parent, original, shape, shape)
    local = tuple(value["local_axis"] for value in source_axes)
    control_values = signed_expectation(control_prediction, local)
    signed_control = {key: control_values[key] for key in ("names", "world_axes")}
    environment, source_lights = source_scene(shape.native.LinkValue)
    intents = [light_values(row) for row in source_lights]
    previous_generated = old_prediction["generated"]
    previous_signed = signed_expectation(previous_generated, ((0.0, 0.0, 1.0),) * 2)
    positive = check_live_signs(old, previous_signed, signed_control)
    saved = old["phases"]["Generated"]["saved"]
    old_hashes = {"parent": saved["parent"], "child": saved["child"]["native_sha256"]}
    old_saved = check_saved(baseline_root / "Working" / previous["working_names"]["parent"],
                            baseline_root / "Working" / previous["working_names"]["child"],
                            old_hashes, previous_signed, previous_generated)
    flipped = {**previous_signed, "world_axes": [tuple(-value for value in axis) for axis in previous_signed["world_axes"]]}
    try:
        check_live_signs(old, flipped, signed_control)
    except ValueError:
        pass
    else:
        raise ValueError("live independent criterion accepted opposite wrapper signs")
    wrong_bounds = {**previous_signed, "saved_bounds_by_carrier_sign_m": {
        sign: [(near, -far) for near, far in values] for sign, values in previous_signed["saved_bounds_by_carrier_sign_m"].items()
    }}
    try:
        check_saved(baseline_root / "Working" / previous["working_names"]["parent"],
                    baseline_root / "Working" / previous["working_names"]["child"],
                    old_hashes, wrong_bounds, previous_generated)
    except ValueError:
        pass
    else:
        raise ValueError("saved independent criterion accepted the reversed physical extent")

    cases = {}
    for index, (case, (filename, expected_digest)) in enumerate(FIXTURES.items()):
        path = checked(REPO / "re/solidworks/inputs" / filename, expected_digest)
        fixture = FromData(json.loads(path.read_bytes()))
        if case == "Aligned":
            document = neutral_d01(fixture, parent, source_axes, shape, "SignedD01Aligned")
            axes, edit_depth = local, previous_generated["edited_depth_m"]
        else:
            document = neutral_contrast(fixture)
            axes, edit_depth = ((0.0, 0.0, -1.0),) * 2, 0.01874901
        prediction = generated_prediction(document, control_prediction, independent_protocol(document, edit_depth))
        expected = signed_expectation(prediction, axes)
        cases[case] = stage_case(out / case, baseline_root, previous, runtime, controls, source_closure, document, axes, environment,
                                intents, {"generated": prediction, "control": control_prediction}, expected,
                                signed_control, written_at + index, case)
    require(inventory_receipt(source_inventory(REPO)) == source_closure, "the frozen source closure changed")
    result = {"schema": "kit.sw2026.signed-wrapper-native-discriminator.v1", "writer_revision": REVISION,
              "preparer_sha256": digest(Path(__file__)), "source_closure": source_closure, "baseline_trial_sha256": OLD_TRIAL,
              "baseline_result_sha256": OLD_RESULT, "cases": cases, "native_processes_started": 0,
              "sealed_inputs_read": 0, "whole_source_acceptance": False,
              "host_postflight_self_check": {"previous_live_axis_checks": positive,
                                              "previous_saved": old_saved, "refused_opposite_live_axis": True,
                                              "refused_opposite_saved_extent": True}}
    write_json(out / "HostPreparation.json", result)
    return result


def postflight(trial, trial_sha):
    job = json.loads(checked(trial, trial_sha).read_bytes())
    root = trial.resolve().parent
    require(job["writer_revision"] == REVISION and job["oracle_sha256"] == ORACLE
            and job["preparer_sha256"] == digest(Path(__file__))
            and job["source_closure"] == inventory_receipt(source_inventory(REPO)),
            "the exact signed packet and evaluator closure are required")
    for name, wanted in job["files_sha256"].items():
        checked(root / name, wanted)
    for role, name in job["working_names"].items():
        checked(root / "Frozen" / name, job["generated_sha256"][role])
        checked(Path(job["controls"][role]["host_path"]), job["controls"][role]["sha256"])
    result_path = root / "Result.json"
    result = json.loads(result_path.read_bytes())
    require(result["packet_sha256"] == trial_sha, "the native report does not belong to this packet")
    for role in ROLES:
        record = json.loads((root / "Inspection" / role / "Record.json").read_bytes())
        require(record["job"] == {"phase": role, "packet_sha256": trial_sha}
                and record["result"] == result["phases"][role], "the native phase record or aggregate differs")
    expected = json.loads((root / "Evidence/ExpectedSigned.json").read_bytes())
    prediction = json.loads((root / "Evidence/Prediction.json").read_bytes())
    validate_prediction(prediction["generated"])
    live_checks = check_live_signs(result, expected["generated"], expected["control"])
    files = result["phases"]["Generated"]["saved"]
    names = job["working_names"]
    hashes = {"parent": files["parent"], "child": files["child"]["native_sha256"]}
    saved = check_saved(root / "Working" / names["parent"], root / "Working" / names["child"], hashes,
                       expected["generated"], prediction["generated"])
    return {"case": job["case"], "passed": True, "packet_sha256": trial_sha,
            "native_result_sha256": digest(result_path), "live_signed_axis_checks": live_checks,
            "saved_parent_child_sha256": hashes, "saved_signed": saved,
            "heldout_acceptance": False, "whole_source_acceptance": False}


def main():
    parser = argparse.ArgumentParser(description="Stage and check the signed concentric wrapper native discovery packets")
    commands = parser.add_subparsers(dest="command", required=True)
    stage = commands.add_parser("prepare")
    stage.add_argument("prior_radial_packet", type=Path)
    stage.add_argument("new_packet_root", type=Path)
    stage.add_argument("--written-at", type=int, required=True)
    after = commands.add_parser("postflight")
    after.add_argument("trial", type=Path)
    after.add_argument("sha256")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.prior_radial_packet, args.new_packet_root.resolve(), args.written_at)
    else:
        result = postflight(args.trial, args.sha256)
        output = args.trial.resolve().parent / "SignedPostflight.json"
        require(not output.exists(), "preserve the earlier signed postflight result")
        write_json(output, result)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
