import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath


def read(path):
    content = path.read_bytes()
    return json.loads(content), sha256(content).hexdigest()


def measurement(raw):
    return {
        "features": raw["timeline"],
        "bodies": [{
            "name": item["name"],
            "volume_mm3": item["volume_cm3"] * 1000,
            "center_mm": [coordinate * 10 for coordinate in item["center_cm"]],
            "faces": item["topology"][0],
            "edges": item["topology"][1],
            "vertices": item["topology"][2],
            "bounds_mm": [[coordinate * 10 for coordinate in item[key]] for key in ("min_cm", "max_cm")],
        } for item in raw["bodies"]],
        "sketches": [{
            "name": item["name"],
            "entities": len(item["lines_cm"]),
            "constraints": len(item["constraints"]),
            "dimensions": len(item["dimensions"]),
        } for item in raw["sketches"]],
        "parameters": [{
            "name": item["name"],
            "value": item["internal_value"],
            "display_unit": item["display_unit"],
            "unit": {"mm": "cm", "deg": "rad"}.get(item["display_unit"], item["display_unit"]),
            "expression": item["expression"],
        } for item in raw["model_parameters"]],
    }


def record(raw, archive_sha):
    states = raw["measurements"]
    result = {
        "application": "fusion",
        "build": raw["fusion_version"],
        "pid": raw["pid"],
        "source_sha256": archive_sha,
        "status": "measured" if raw["status"] == "passed" else "failed",
        "load_errors": [],
        "edits": [],
        "documents_after": raw.get("documents_after"),
    }
    for label in ("opened", "rebuilt"):
        if label in states:
            result[label] = measurement(states[label])
    if "error" in raw:
        result["error"] = raw["error"].splitlines()[-1]
        if raw.get("last_operation", "").startswith("import "):
            result["load_errors"].append(result["error"])
    return result


def make_receipt(batch, run):
    config, config_sha = read(batch / "Batch.json")
    manifest, _ = read(run / "manifest.json")
    role = config["role"]
    source_sha = config["source_sha256"]
    candidate_sha = config["candidate_sha256"]
    if (manifest["application"] != "fusion" or manifest["source_sha256"] != source_sha
            or manifest["candidate_sha256"][role] != candidate_sha):
        raise ValueError("the oracle batch did not measure this Fusion round-trip artifact")

    stages, stage_hashes = {}, {}
    for name in ("ControlBefore", "Candidate", "Reopen", "ControlAfter"):
        path = batch / f"{name}.json"
        if name == "Reopen" and not path.exists() and stages["Candidate"]["status"] != "passed":
            continue
        raw, stage_hash = read(path)
        if (raw["stage"] != name or raw["status"] not in ("passed", "failed")
                or type(raw["pid"]) is not int or raw["pid"] <= 0 or raw["batch_sha256"] != config_sha
                or raw["source_sha256"] != source_sha or raw["candidate_sha256"] != candidate_sha
                or raw["measurement_script_sha256"] != config["measurement_script_sha256"]):
            raise ValueError(f"{name} receipt does not bind this completed oracle stage")
        if raw["status"] == "passed":
            for count_key in ("documents_before", "documents_after"):
                count = raw.get(count_key)
                if type(count) is not int or count != 0:
                    raise ValueError(f"{name} passed receipt requires zero open documents")
        stages[name], stage_hashes[name] = raw, stage_hash
    before, after = stages["ControlBefore"], stages["ControlAfter"]
    control_sha = before["archives"]["VendorControl.f3d"]
    if after["archives"]["VendorControl.f3d"] != control_sha:
        raise ValueError("control archive changed between native measurements")
    if len({raw["fusion_version"] for raw in stages.values()}) != 1 or len({raw["pid"] for raw in stages.values()}) != len(stages):
        raise ValueError("oracle stages lack distinct process IDs and a common Fusion build")

    observed = stages["Candidate"]
    candidate = record(observed, candidate_sha)
    if observed["status"] == "passed":
        candidate_name = PureWindowsPath(config["candidate"]).name
        if observed["archives"].get(candidate_name) != candidate_sha:
            raise ValueError("candidate stage measured different archive bytes")
        reopened = stages["Reopen"]
        if reopened["status"] != "passed":
            candidate["status"] = "failed"
            candidate["error"] = "Fusion could not rebuild both saved variants in a new process"
        else:
            for archive in ("VendorEdited.f3d", "VendorRestored.f3d"):
                saved_sha = observed["archives"].get(archive)
                if saved_sha is None or reopened["archives"].get(archive) != saved_sha:
                    raise ValueError(f"{archive} changed between save and fresh-process reopen")
            edited = observed["measurements"]["edited"]
            restored = observed["measurements"]["restored"]
            candidate["edits"].append({
                "parameter": "kitHeight",
                "original_value": restored["user_parameters"]["kitHeight"]["internal_value"],
                "edited_value": edited["user_parameters"]["kitHeight"]["internal_value"],
                "unit": "cm",
                "measured": measurement(edited),
                "saved": "VendorEdited.f3d",
                "saved_sha256": observed["archives"]["VendorEdited.f3d"],
                "restored": measurement(restored),
                "restored_sha256": observed["archives"]["VendorRestored.f3d"],
                "reopen_pid": reopened["pid"],
                "reopened": measurement(reopened["measurements"]["edited_reopened"]),
                "restored_reopened": measurement(reopened["measurements"]["restored_reopened"]),
            })
    return {
        "schema": 1,
        "application": "fusion",
        "role": role,
        "run_fingerprint": manifest["run_fingerprint"],
        "source_sha256": source_sha,
        "candidate_sha256": candidate_sha,
        "sdk_revision": manifest["sdk_revision"],
        "controls": {"before": record(before, control_sha), "after": record(after, control_sha)},
        "candidate": candidate,
        "fusion_oracle_stage_sha256": stage_hashes,
    }


def main():
    parser = argparse.ArgumentParser(description="Bind Fusion oracle receipts to an encoder manifest.")
    parser.add_argument("batch", type=Path)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = make_receipt(args.batch, args.run)
    with args.output.open("x", encoding="utf-8", newline="\n") as destination:
        destination.write(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
