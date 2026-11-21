from argparse import ArgumentParser
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def functions(path):
    return {node.name: sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() for node in ast.parse(path.read_bytes()).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def require(value, message):
    if not value:
        raise ValueError(message)


def freeze(args):
    prior = args.prior_root.resolve(strict=True)
    output = args.output.resolve()
    require(prior.name == "GeneratedThroughAll01" and output.name == "GeneratedThroughAll02" and prior.parent == output.parent, "the retry preserves the declared original native input custody")
    require(digest(prior / "Trial.json") == args.prior_sha256, "the original frozen packet changed")
    old = json.loads((prior / "Trial.json").read_bytes())
    require(old["schema"] == "kit.sw2026.generated-through-all-native.v1" and old["heldout_payloads_read"] == 0, "only the disclosed original through-all packet is admitted")
    if args.check:
        require(output.is_dir(), "the checked retry must already exist")
    else:
        output.mkdir(exist_ok=False)
    for relative, pin in old["files_sha256"].items():
        source = prior / relative
        require(digest(source) == pin, "original native input or prediction changed")
        target = output / relative
        if args.check:
            require(digest(target) == pin, "the retry copy differs from its original")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    if args.check:
        for name, pin in old["tools_sha256"].items():
            if name != "InspectThroughAllCold.py":
                require(digest(output / "Tools" / name) == pin, "an unrelated oracle helper changed")
    else:
        shutil.copytree(prior / "Tools", output / "Tools")
        shutil.copyfile(args.observer, output / "Tools/InspectThroughAllCold.py")
    require(digest(output / "Tools/InspectThroughAllCold.py") == digest(args.observer), "the retry observer differs")
    phases = []
    for name in ("ControlBefore", "ControlAfter"):
        path = prior / "Inspection" / name / "Record.json"
        row = json.loads(path.read_bytes())
        require(row["stage"] == "starting" and not row["api_calls"] and "result" not in row, "the original evidence is not the expected pre-native observer failure")
        phases.append({"phase": name, "record_sha256": digest(path), "stage": row["stage"], "api_calls": len(row["api_calls"]), "numeric_checks": len(row["checks"]), "result_present": False, "native_identity_present": False})
    old_functions, new_functions = functions(prior / "Tools/InspectThroughAllCold.py"), functions(args.observer)
    unchanged = {key: old_functions[key] for key in ("snapshot", "native_case", "api_metadata", "ui_tree")}
    require(all(new_functions[key] == value for key, value in unchanged.items()), "the observer retry changed a measurement or prediction rule")
    failure = {"schema": "kit.sw2026.through-all-native-observer-prelaunch-failure.v1", "previous_packet_sha256": args.prior_sha256, "previous_observer_sha256": digest(prior / "Tools/InspectThroughAllCold.py"), "registered_metadata_sha256": digest(prior / "ApiMetadata.json"), "native_processes_started": 0, "native_controls_measured": 0, "generated_candidate_opened": False, "native_generated_acceptance": False, "observer_failure": "Windows path rendering was used as a POSIX-keyed manifest lookup before native launch; original summary also required a result member absent from partial records", "phases": phases, "preserved_unchanged_measurement_functions": unchanged, "writer_source_manifest_sha256": old["writer_source_manifest_sha256"], "candidate_sha256": old["files_sha256"][old["generated_file"]], "generated_case_sha256": old["files_sha256"]["GeneratedCase.json"], "original_evidence_preserved": True}
    failure_bytes = encoded(failure)
    failure_path = output / "ObserverFailure01.json"
    if args.check:
        require(failure_path.read_bytes() == failure_bytes, "the original failure receipt changed")
    else:
        failure_path.write_bytes(failure_bytes)
    job = {**old, "files_sha256": {**old["files_sha256"], "ObserverFailure01.json": sha256(failure_bytes).hexdigest()}, "tools_sha256": {path.name: digest(path) for path in sorted((output / "Tools").glob("*.py"))}, "original_native_inputs": {"packet_name": prior.name, "packet_sha256": args.prior_sha256, "encoded_generated_path": json.loads((prior / "GeneratedCase.json").read_bytes())["recipe"]["native_path"], "custody": "open original immutable native input paths; save edited derivatives only under this retry packet"}, "observer_retry": {"number": 2, "previous_packet_sha256": args.prior_sha256, "constructor_and_predictions_unchanged": True, "only_observer_path_custody_and_partial_summary_changed": True}}
    job_bytes = encoded(job)
    pin = sha256(job_bytes).hexdigest()
    old_recipe = json.loads((prior / "Recipe.json").read_bytes())
    recipe = {**old_recipe, "packet_sha256": pin, "observer_only_retry": True, "original_packet_sha256": args.prior_sha256, "original_native_paths_preserved": True}
    for row in recipe["commands"]:
        row["argv"] = [value.replace("GeneratedThroughAll01\\Tools", "GeneratedThroughAll02\\Tools").replace("GeneratedThroughAll01\\Trial.json", "GeneratedThroughAll02\\Trial.json") if isinstance(value, str) else value for value in row["argv"]]
        row["argv"] = [pin if value == args.prior_sha256 else value for value in row["argv"]]
    recipe_bytes = encoded(recipe)
    if args.check:
        require((output / "Trial.json").read_bytes() == job_bytes and (output / "Recipe.json").read_bytes() == recipe_bytes, "the retry recipe does not reproduce")
    else:
        (output / "Trial.json").write_bytes(job_bytes)
        (output / "Recipe.json").write_bytes(recipe_bytes)
    return {"passed": True, "packet_sha256": pin, "recipe_sha256": sha256(recipe_bytes).hexdigest(), "observer_sha256": digest(args.observer), "candidate_sha256": old["files_sha256"][old["generated_file"]], "native_processes_started": 0, "heldout_payloads_read": 0}


parser = ArgumentParser(description="Freeze or verify an observer-only disclosed through-all retry without changing native inputs")
parser.add_argument("--prior-root", type=Path, required=True)
parser.add_argument("--prior-sha256", required=True)
parser.add_argument("--observer", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--check", action="store_true")
print(json.dumps(freeze(parser.parse_args()), sort_keys=True))
