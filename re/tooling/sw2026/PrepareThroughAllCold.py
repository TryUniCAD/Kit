from argparse import ArgumentParser
import ast
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import shutil
import sys

base = Path(__file__).parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def dependency_closure(tools, initial):
    result = set(initial)
    pending = list(initial)
    while pending:
        filename = pending.pop()
        module = ast.parse((tools / filename).read_bytes())
        for node in ast.walk(module):
            names = [item.name.split(".")[0] for item in node.names] if isinstance(node, ast.Import) else [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else []
            for name in names:
                candidate = name + ".py"
                if (tools / candidate).is_file() and candidate not in result:
                    result.add(candidate)
                    pending.append(candidate)
    return sorted(result)


def check_source():
    manifest = json.loads((base / "MethodSourceManifest02.json").read_bytes())
    for relative, expected in manifest["source_files"].items():
        assert digest(base / "CodeRoot" / relative) == expected["sha256"], relative
    for relative, expected in manifest["inputs"].items():
        assert digest(base / relative) == expected["sha256"], relative
    proof = json.loads((base / "Process02/Result.json").read_bytes())
    assert proof["passed"] and proof["workers"] == 31 and not proof["heldout_payloads_read"]
    return proof


def tree_prediction(recipe, tools):
    sys.path[:0] = [str(base / "CodeRoot/src"), str(tools)]
    from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree
    from InspectSdkBlindPart import tree_prediction

    axis = recipe["axis"]
    settings = DefaultPartTree({"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}[axis], recipe["written_at"], axis)
    request = {"settings": {"system": {"folders": settings.FolderValues, "cabinet_name": settings.CabinetName, "planes": dict(settings.PlaneNames), "origin_name": settings.OriginName}}}
    rows = tree_prediction(request, {"intent": {"profile": "StockProfile", "feature": "StockBoss", "resolved_roots": 19}})
    return [*rows, ["ThroughProfile", "ProfileFeature", None], ["ThroughFeature", "ICE", None]]


def main():
    global base
    parser = ArgumentParser(description="Freeze the disclosed source-only G01 through-all cut and its independent native lifecycle")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--preparation-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--observer-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.preparation_root.resolve(strict=True)
    repo = args.repository.resolve(strict=True)
    output = args.output.resolve()
    assert output.name == "GeneratedThroughAll01" and not output.exists()
    proof = check_source()
    public_lock = base / "ThroughAllSourceLock01.json"
    assert digest(public_lock) == "3efe141cd31cc06e8b7545db590548dd1ba511960261e8b78cf72523d5d5ba79"
    recipe = json.loads((base / "Inputs/G01.json").read_bytes())
    expected = json.loads((base / "Inputs/G01Prediction.json").read_bytes())
    target = PureWindowsPath(recipe["native_path"])
    assert target.parent.name == "GeneratedInput" and target.parent.parent.name == output.name
    generated = base / "Process02/Generated" / target.name
    row = next(item for item in proof["positive_cases"] if item["case"] == "G01")
    assert digest(generated) == row["artifact_sha256"]
    disclosed = args.source_root.resolve(strict=True)
    assert disclosed.name == "D01" and disclosed.parent.name == "Disclosed" and disclosed.parent.parent.name == "ThroughAllSourcePacket03"
    control = disclosed / "Native/Source/ThroughAllD01CutForward.SLDPRT"
    source_lock = next(item for item in json.loads(public_lock.read_bytes())["slots"] if item["slot"] == "D01")
    assert digest(control) == source_lock["native_artifacts"]["source"]["sha256"]
    source_manifest = disclosed / "SavedAuthor.json"
    assert digest(source_manifest) == source_lock["source_manifest_sha256"]
    authored = json.loads(source_manifest.read_bytes())
    sys.path.insert(0, str(repo / "re/tooling/sw2026"))
    from ThroughAllSourcePlan import disclosed_cases, geometry

    source = next(item for item in disclosed_cases() if item["id"] == "D01")
    control_recipe = {"name": source["name"], "configuration": "Default", "axis": "z", "stock_size_m": source["stock_size_m"], "stock_center_m": source["stock_center_m"], "circle_center_m": source["circle_center_m"], "radius_m": source["radius_m"], "direction": source["direction"], "written_at": recipe["written_at"]}
    control_expected = {}
    for state, edited in (("source", False), ("edited", True)):
        predicted = geometry(source, edited)
        control_expected[state] = {key: predicted[key] for key in ("body_count", "volume", "area", "com")}
        control_expected[state]["stock_depth_m"] = source["edit_stock_depth_m"] if edited else source["stock_size_m"][2]
    tools = repo / "re/tooling/sw2026"
    expected_tree = tree_prediction(recipe, tools)
    assert [[item["name"], item["type"], item["parent"]] for item in authored["source"]["tree"]] == expected_tree
    output.mkdir()
    target_file = output / "GeneratedInput" / target.name
    target_file.parent.mkdir()
    shutil.copyfile(generated, target_file)
    source_file = output / "Control" / control.name
    source_file.parent.mkdir()
    shutil.copyfile(control, source_file)
    write(output / "GeneratedCase.json", {"recipe": recipe, "prediction": expected["independent_analytic_geometry"], "expected_tree": expected_tree, "source": "independently authored neutral recipe and analytic prediction", "heldout_payloads_read": 0})
    write(output / "ControlCase.json", {"recipe": control_recipe, "prediction": control_expected, "expected_tree": expected_tree, "source_manifest_sha256": digest(source_manifest), "source": "exact disclosed D01 source control", "heldout_payloads_read": 0})
    for source_path, filename in ((base / "Process02/Result.json", "BuildProof.json"), (base / "MethodSourceManifest02.json", "WriterSourceManifest.json"), (public_lock, "ThroughAllSourceLock01.json")):
        shutil.copyfile(source_path, output / filename)
    tool_names = dependency_closure(tools, ("ThroughAllAuthor.py", "ThroughAllApiMetadata.py", "AuthorCurves.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py"))
    dest_tools = output / "Tools"
    dest_tools.mkdir()
    for name in tool_names:
        shutil.copyfile(tools / name, dest_tools / name)
    inspector = args.observer_source.resolve(strict=True)
    shutil.copyfile(inspector, dest_tools / inspector.name)
    files = {path.relative_to(output).as_posix(): digest(path) for path in sorted(output.rglob("*")) if path.is_file() and path.parent != dest_tools}
    job = {"schema": "kit.sw2026.generated-through-all-native.v1", "oracle_sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe", "generated_file": target_file.relative_to(output).as_posix(), "control_file": source_file.relative_to(output).as_posix(), "writer_source_manifest_sha256": digest(output / "WriterSourceManifest.json"), "source_lock_sha256": digest(public_lock), "files_sha256": files, "tools_sha256": {path.name: digest(path) for path in sorted(dest_tools.glob("*.py"))}, "heldout_payloads_read": 0, "native_acceptance_at_freeze": False, "scope": "disclosed ordinary forward through-all circular cut in finite mid-plane stock; complete native lifecycle", "writer_revision": None}
    job_file = output / "Trial.json"
    write(job_file, job)
    relative_root = r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\GeneratedThroughAll01"
    program = relative_root + r"\Tools\InspectThroughAllCold.py"
    command = ["py", "-3.12", program, "--packet", relative_root + r"\Trial.json", "--packet-sha256", digest(job_file)]
    commands = [{"name": action, "argv": [*command, "--action", action]} for action in ("verify", "metadata")]
    commands.extend({"name": name, "argv": [*command, "--action", "phase", "--phase", name]} for name in ("ControlBefore", "Generated", "Reopen", "ControlAfter"))
    commands.append({"name": "summarize", "argv": [*command, "--action", "summarize"]})
    write(output / "Recipe.json", {"schema": "kit.sw2026.generated-through-all-native-recipe.v1", "packet_sha256": digest(job_file), "commands": commands, "run_serially": True, "always_run_after_control_independently": True, "skip_reopen_if_generation_failed": True, "source_and_tools_immutable": True, "native_processes_started": 0, "heldout_payloads_read": 0})
    print(json.dumps({"packet": str(job_file), "packet_sha256": digest(job_file), "recipe_sha256": digest(output / "Recipe.json"), "generated_sha256": digest(target_file), "observer_sha256": digest(dest_tools / inspector.name), "tools": len(job["tools_sha256"]), "native_processes_started": 0}))


if __name__ == "__main__":
    main()
