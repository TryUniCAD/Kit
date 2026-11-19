import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys


SW2026 = Path(__file__).resolve().parents[2]
REPO = SW2026.parents[2]
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from ConcentricNativeContract import ORACLE, ROLES, checked, digest, require, write_json
from ConcentricNeutralAdmission import bind_cylinder, project_concentric
from ConcentricSourcePlan import disclosed_cases, expected_transforms, geometry
from PrepareGeneratedConcentric import generated_prediction, input_row, windows_path
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import PutPartRefsMut
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from interchange import frozen_mapping
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from para.concentric.CheckConcentricAssembly import verify_emission
from para.concentric.ConcentricAssembly import principal_planes
from para.concentric.ConcentricMate import make_concentric
from para.concentric.PrepareConcentricPersistence import derive_session
from para.concentric.ProjectConcentricRadialIntent import (
    SOURCE_FEATURE_NEUTRAL, BindPartIntent, MakeCirclePart, MakePartRecipe, ProjectCircle,
    SelfFileInput, attach_scene, check_archives, read_intents,
)
from para.cylinder.CylinderAttachment import attach_cylinder_mut


BASELINE = "9b7e52d198a7e2a70902b3794fff1987451bc6a599ca1d557493eddc75a580c9"
REQUEST = "d25e6b4bdd6631c8c40aeae0335f96cebcbc740af0151dd7154ae08a873a6ca1"
STANDALONE = "deced53cda69c8b769112baeccfd4900a1f6533c23163a7b4124bb4e274d9ba8"
ROOT_NAME = "RadialConcentricProbe"
MATE_NAME = "ConcentricRadialProbe"


def matrix_values(native):
    return tuple(native[col * 3 + row] if col < 3 else native[9 + row] * 1000
                 for row in range(3) for col in range(4)) + (0., 0., 0., 1.)


def author_parent(child, case):
    fixture = checked(REPO / "re/solidworks/inputs/ConcentricFeatureNeutral01.json", SOURCE_FEATURE_NEUTRAL)
    seed = FromData(json.loads(fixture.read_bytes()))
    graph = seed.assembly
    root_id = graph.root_definition_id
    child_name = child.metadata["name"]
    definitions = tuple(replace(row, name=ROOT_NAME if row.id == root_id else child_name) for row in graph.definitions)
    placements = expected_transforms(case)
    instances = tuple(replace(row, name=f"{child_name}-{row.order + 1}",
                              transform=replace(row.transform, values=matrix_values(placements[row.order])))
                      for row in graph.instances)
    entities = tuple(replace(row, radius=case["radius_m"] * 1000) for row in graph.mate_entities)
    mate, = graph.mates
    mate = replace(mate, name=MATE_NAME)
    document = replace(
        seed, metadata=frozen_mapping({"name": ROOT_NAME}),
        assembly=replace(graph, definitions=definitions, instances=instances, mate_entities=entities, mates=(mate,),
                         documents=(replace(graph.documents[0], document=child),)),
    )
    document.AssertValid()
    return document


def make_bundle(document, child, scene, lights, destination, written_at):
    model = ReadAsmModel(document)
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, destination, written_at)
    part_plan = ProjectCircle(child)
    require(not part_plan.IsDiameter and part_plan.AxisValue == "z" and part_plan.PlaneName == "Front Plane"
            and part_plan.EndValue.ModeValue == "blind" and not part_plan.EndValue.IsReversed,
            "expected the disclosed standalone forward radial part")
    basic = MakePartRecipe(part_plan, written_at)
    folders = tuple((kind, scene if kind == "moEnvFolder_c" else name) for kind, name in basic.SystemValue.FolderValues)
    recipe = replace(basic, SystemValue=replace(basic.SystemValue, FolderValues=folders))
    bound = BindPartIntent(child, part_plan, recipe, SelfFileInput(paths.ChildValue.PathName, written_at))
    session, updates = derive_session(child, written_at)
    attachment = attach_cylinder_mut(MakeCirclePart(child, bound), session, updates, 0,
                                     tessellated_faces=True, driver_mode="radius")
    base = attachment.candidate
    part = attach_scene(base, lights, bound.TargetValue)
    attachment = replace(attachment, candidate=part)
    nodes = {node.index: XmtNode(node.index, node.kind, node.fields) for node in attachment.projection.partition.nodes}
    binding = bind_cylinder(child, part, nodes, profile="derived_feature", driver_mode="radius")
    intent = project_concentric(document, {model.ChildValue.id: binding})
    metadata = MakeAsmRecipe(model, recipe, principal_planes(document, written_at), paths.ParentValue)
    placements = tuple(ReadAsmPlace(row) for row in model.Occurrences)
    state = MakeAsmBase(metadata)
    headers = MakeAsmHeaders(state, metadata)
    references = PutPartRefsMut(state, part, metadata, placements, headers)
    selected = tuple(row.occurrence_index for row in intent.ends)
    mate = make_concentric(state, metadata, headers, tuple(references[index] for index in selected),
                           tuple(row.placement.FrameValue for row in intent.ends), attachment, intent.mate.name,
                           intent.alignment_code, intent.rotation_locked, selected.index(intent.fixed_index))
    parent = BuildSldprt(EmitAsmStreams(state, part, metadata, headers, references, (mate,)).StreamsValue, FormatVersion=4)
    names = tuple(row.occurrence.name for row in intent.ends)
    child_proof = check_archives(part, base, part_plan, lights)
    parent_proof = verify_emission(parent, attachment, intent.alignment_code, intent.rotation_locked, intent.fixed_index, names)
    return {"parent": parent, "child": part.BytesValue}, {"parent": parent_proof, "child": child_proof}


def guarded_bundle(document, child, scene, lights, destination, written_at):
    import codecs

    from convert.adapters.base.WritePolicy import GetDocumentCaps

    GetDocumentCaps(child)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    active = True
    attempted = []

    def guard(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempted.append(event)
            raise RuntimeError("guarded concentric construction attempted runtime I/O: " + event)

    sys.addaudithook(guard)
    try:
        files, proof = make_bundle(document, child, scene, lights, destination, written_at)
        repeated, repeated_proof = make_bundle(document, child, scene, lights, destination, written_at)
        require(files == repeated and proof == repeated_proof, "repeated from-neutral assembly construction changed")
    finally:
        active = False
    require(not attempted, "guarded assembly generation attempted a file, process or network call")
    proof.update(runtime_io_attempts=len(attempted), builds=2, native_processes_started=0,
                 direct_full_source_admitted=False, heldout_credit=0, id_allocation="fresh first tags and no preceding faces")
    return files, proof


def predict(document, case, control, standalone):
    result = standalone["phases"]["Generated"]
    target = result["edited"]["shape"]["extrusion"]["depth"]
    edit = dict(case, edited_depth_m=target, slide_edit_m=0., spin_edit_rad=0.)

    def as_protocol(value):
        return {role: {"bodies": 1 if role == "child" else 2, "volume_m3": row["volume"],
                       "area_m2": row["area"], "center_m": row["com"]}
                for role, row in value.items() if role in {"child", "assembly"}}

    protocol = {"depth_edit": {"target_m": target, "expected_geometry": as_protocol(geometry(edit, True))},
                "expected_readback": {"occurrence_order": [row.name for row in document.assembly.instances],
                                      "fixed_flags": [True, False], "mate_name": MATE_NAME, "com_mate_alignment": 0,
                                      "rotation_locked": False, "depth_m": case["depth_m"], "radius_m": case["radius_m"],
                                      "expected_geometry": as_protocol(geometry(case))}}
    generated = generated_prediction(document, control, protocol)
    proved_child_tree = [[row["name"], row["type"], row["parent"]] for row in result["rebuilt"]["tree"]]
    require(generated["child_tree"] == proved_child_tree, "full declared child tree differs from the measured standalone pair")
    return {"control": control, "generated": generated}


def prepare(args):
    baseline_path = checked(args.baseline, BASELINE).resolve()
    previous = json.loads(baseline_path.read_bytes())
    old_root = baseline_path.parent
    control_path = checked(old_root / "Evidence/Prediction.json", previous["files_sha256"]["Evidence/Prediction.json"])
    control = json.loads(control_path.read_bytes())["control"]
    data = json.loads(checked(args.request, REQUEST).read_bytes())
    standalone = json.loads(checked(args.standalone, STANDALONE).read_bytes())
    require(standalone["passed"] is True and standalone["distinct_native_processes"] == 4,
            "the standalone radial source and scene lifecycle must pass first")
    child = FromData(data["child"])
    case = next(row for row in disclosed_cases() if row["id"] == "D01")
    document = author_parent(child, case)
    lights = read_intents(data["lights"], args.written_at)
    names = {"parent": ROOT_NAME + ".SLDASM", "child": child.metadata["name"] + ".SLDPRT"}
    out = args.output.resolve()
    require(not out.exists(), "use a new owned packet directory")
    destination = windows_path(out / "Working" / names["parent"])
    predictions = predict(document, case, control, standalone)
    files, proof = guarded_bundle(document, child, data["environment_name"], lights, destination, args.written_at)
    out.mkdir(parents=True, exist_ok=False)
    evidence = out / "Evidence"
    evidence.mkdir()
    write_json(evidence / "Prediction.json", predictions)
    write_json(evidence / "Neutral.json", {"document": ToData(document), "lighting": data["lights"]})
    write_json(evidence / "Build.json", proof)
    runtime_path = checked(old_root / "Evidence/GuestPython.json", previous["files_sha256"]["Evidence/GuestPython.json"])
    (evidence / "GuestPython.json").write_bytes(runtime_path.read_bytes())
    runtime = json.loads(runtime_path.read_bytes())
    tools = out / "Tools"
    tools.mkdir()
    for path, checksum in previous["files_sha256"].items():
        if path.startswith("Tools/"):
            (out / path).write_bytes(checked(old_root / path, checksum).read_bytes())
    for label in ("Frozen", "Working"):
        (out / label).mkdir()
        for role, name in names.items():
            (out / label / name).write_bytes(files[role])
    controls = {}
    for role, row in previous["controls"].items():
        controls[role] = input_row(Path(row["host_path"]), row["sha256"])
        require(controls[role] == row, "the actual disclosed control locators or bytes changed")
    job = {"schema": previous["schema"], "oracle_sha256": ORACLE, "roles": list(ROLES),
           "require_preference_18_true": True, "controls": controls, "heldout_inputs_read": 0,
           "native_processes_started": 0, "working_names": names,
           "generated_sha256": {key: sha256(value).hexdigest() for key, value in files.items()},
           "files_sha256": {str(path.relative_to(out)): digest(path) for owner in (tools, evidence) for path in owner.iterdir()}}
    trial = out / "Trial.json"
    write_json(trial, job)
    wanted = digest(trial)
    prefix = [runtime["executable"], "-B", windows_path(tools / "ObserveConcentricPersistence.py")]
    location = windows_path(trial)
    commands = {"verify_guest": [*prefix, "verify", location, wanted],
                **{role: [*prefix, "phase", location, wanted, role] for role in ROLES},
                "summary": [*prefix, "summary", location, wanted]}
    write_json(out / "Recipe.json", {"ordered_phases": list(ROLES), "always_run_trailing_control": True, "argv": commands})
    return {"trial": wanted, "recipe": digest(out / "Recipe.json"), "files": job["generated_sha256"], "proof": proof}


def main():
    parser = argparse.ArgumentParser(description="Freeze one disclosed synthetic radial concentric pair")
    for name in ("baseline", "request", "standalone", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--written-at", type=int, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
