import argparse
from dataclasses import replace
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys


SW2026 = Path(__file__).resolve().parents[2]
REPO = SW2026.parents[2]
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from ConcentricNativeContract import ORACLE, ROLES, checked, digest, require, write_json
from PrepareGeneratedConcentric import generated_prediction, input_row, windows_path


BASELINE_SHA256 = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"
AMBIENT_SHA256 = "c178599a0990a89a9ef1e17017150dc5bc1cbd3fdbbf301542e30cbc3c8c7c99"
SCHEMA = "kit.sw2026.concentric-persistence.v1"
OBSERVER = "ObserveConcentricPersistence.py"


def derive_session(child, written_at):
    from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session, Update
    from para.rectangle.ArchiveAttachment import FeatureUpdate

    owners = 1 + len(child.sketches) + len(child.feature_timeline)
    require(owners == 3, "expected the ordinary origin, sketch and blind boss")
    history = (
        DeltaEvent("activation"),
        MarkEvent("activation", "activation", True),
        DeltaEvent("intervening"),
        MarkEvent("intervening", "intervening", False),
        DeltaEvent("geometry"),
        MarkEvent("geometry", "geometry", True),
    )
    operations = (Update.ADVANCE,) * owners + (Update.ATTACH_BODY, Update.TESSELLATE)
    updates = tuple(FeatureUpdate(index, written_at, index + 1, True) for index in range(owners))
    return Session(1, 1, history, operations, written_at, owners), updates


def replace_default_lights(prediction, ambient):
    tree = prediction["child_tree"]
    (environment,) = [row[0] for row in tree if row[1] == "EnvFolder"]
    retained = [
        row for row in tree if row[1] not in {"AmbientLight", "DirectionLight"} or row[2] != environment
    ]
    require(len(tree) - len(retained) == 4, "the known disclosed child tree changed")
    (index,) = [index for index, row in enumerate(retained) if row[1] == "EnvFolder"]
    retained.insert(index + 1, [ambient["ambient"]["NameValue"], "AmbientLight", environment])
    prediction["child_tree"] = retained


def construct(document, guest_parent, written_at, ambient):
    import codecs

    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from para.concentric.CheckConcentricAssembly import verify_emission
    from para.concentric.ConcentricAssembly import prepare_concentric

    graph = document.assembly
    child = graph.documents[0].document
    session, updates = derive_session(child, written_at)
    GetDocumentCaps(child)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    attempted = []
    active = True

    def guard(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempted.append(event)
            raise RuntimeError(f"concentric constructor attempted runtime I/O: {event}")

    sys.addaudithook(guard)
    try:
        first = prepare_concentric(document, guest_parent, written_at, session, updates, 0, ambient=ambient)
        second = prepare_concentric(document, guest_parent, written_at, session, updates, 0, ambient=ambient)
        require(first.assembly == second.assembly and first.attachment.file_bytes == second.attachment.file_bytes,
                "fresh concentric generation did not reproduce its bytes")
        expected_names = tuple(row.name for row in graph.instances)
        proof = verify_emission(first.assembly, first.attachment, 1, False, 0, expected_names)
    finally:
        active = False
    require(not attempted, "runtime I/O was attempted inside generation")
    proof.update(written_at=written_at, runtime_io_attempts=len(attempted), repeats=2,
                 first_body_tag=session.first_tag, first_delta_handle=session.next_delta_handle,
                 prior_face_allocations=0, feature_updates=len(updates),
                 last_fraction_ticks=session.update_fraction)
    return first, proof


def prepare(baseline_path, out, written_at):
    from interchange.serialization.Deserialize import FromData
    from interchange.serialization.EncodeData import ToData

    baseline_path = checked(baseline_path, BASELINE_SHA256).resolve()
    baseline = json.loads(baseline_path.read_bytes())
    origin = baseline_path.parent
    case = baseline["cases"]["Feature"]
    protocol_path = checked(origin / "OriginalProtocol.json", baseline["protocol_sha256"])
    protocol = json.loads(protocol_path.read_bytes())["cases"]["Feature"]
    original = case["evidence"]["Neutral"]
    neutral_path = checked(origin / original["path"], original["sha256"])
    document = FromData(json.loads(neutral_path.read_bytes()))
    graph = document.assembly
    child_name = graph.documents[0].document.metadata["name"]
    instances = tuple(replace(row, name=f"{child_name}-{row.order + 1}") for row in graph.instances)
    require([row.order for row in instances] == [0, 1], "unexpected disclosed occurrence order")
    document = replace(document, assembly=replace(graph, instances=instances))
    document.AssertValid()
    protocol["expected_readback"]["occurrence_order"] = [row.name for row in instances]
    old_predictions = json.loads(checked(origin / case["prediction_path"], case["prediction_sha256"]).read_bytes())
    control = old_predictions["control"]
    prediction = generated_prediction(document, control, protocol)
    ambient_path = checked(REPO / "re/solidworks/inputs/PrismAuthoredAmbient01.json", AMBIENT_SHA256)
    ambient = json.loads(ambient_path.read_bytes())
    replace_default_lights(prediction, ambient)
    leaf_names = {"parent": document.metadata["name"] + ".SLDASM", "child": child_name + ".SLDPRT"}
    require(all(PureWindowsPath(name).name == name for name in leaf_names.values()), "nonlocal output basename")
    out = out.resolve()
    require(not out.exists(), "use an unused private trial directory")
    guest_parent = windows_path(out / "Working" / leaf_names["parent"])
    generated, proof = construct(document, guest_parent, written_at, ambient)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out.mkdir(parents=True, exist_ok=False)
    tools = out / "Tools"
    tools.mkdir()
    for name, wanted in baseline["tools_sha256"].items():
        payload = checked(SW2026 / name, wanted).read_bytes()
        (tools / name).write_bytes(payload)
    for name in (OBSERVER, Path(__file__).name):
        (tools / name).write_bytes(Path(__file__).with_name(name).read_bytes())
    evidence = out / "Evidence"
    evidence.mkdir()
    write_json(evidence / "Prediction.json", {"control": control, "generated": prediction})
    write_json(evidence / "Neutral.json", ToData(document))
    write_json(evidence / "Build.json", proof)
    (evidence / "Ambient.json").write_bytes(ambient_path.read_bytes())
    runtime = baseline["guest_runtime"]
    (evidence / "GuestPython.json").write_bytes(checked(origin / runtime["receipt_path"], runtime["receipt_sha256"]).read_bytes())
    controls = {}
    for role in leaf_names:
        known = case["inputs"][f"control_{role}"]
        controls[role] = input_row(Path(known["host_path"]), known["sha256"])
        require(controls[role] == known, "the frozen control locators changed")
    expected_outputs = {"parent": generated.assembly, "child": generated.attachment.file_bytes}
    for directory in ("Frozen", "Working"):
        (out / directory).mkdir()
        for role, name in leaf_names.items():
            with (out / directory / name).open("xb") as file:
                file.write(expected_outputs[role])
    job = {
        "schema": SCHEMA, "oracle_sha256": ORACLE, "roles": list(ROLES),
        "heldout_inputs_read": 0, "native_processes_started": 0,
        "source_head_at_preparation": commit, "baseline_trial_sha256": BASELINE_SHA256,
        "require_preference_18_true": True, "controls": controls,
        "files_sha256": {str(path.relative_to(out)): digest(path) for root in (tools, evidence) for path in root.iterdir()},
        "working_names": leaf_names,
        "generated_sha256": {key: digest(out / "Frozen" / name) for key, name in leaf_names.items()},
    }
    packet = out / "Trial.json"
    write_json(packet, job)
    packet_digest = digest(packet)
    launcher = [runtime["executable"], "-B", windows_path(tools / OBSERVER)]
    guest_packet = windows_path(packet)
    commands = {
        "verify_guest": [*launcher, "verify", guest_packet, packet_digest],
        **{role: [*launcher, "phase", guest_packet, packet_digest, role] for role in ROLES},
        "summary": [*launcher, "summary", guest_packet, packet_digest],
    }
    recipe = out / "Recipe.json"
    write_json(recipe, {"ordered_phases": list(ROLES), "always_run_trailing_control": True, "argv": commands})
    return {"trial_sha256": packet_digest, "recipe_sha256": digest(recipe), "files": job["generated_sha256"],
            "proof": proof, "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze a disclosed neutral-derived concentric persistence packet")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--written-at", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline, args.output, args.written_at), sort_keys=True))


if __name__ == "__main__":
    main()
