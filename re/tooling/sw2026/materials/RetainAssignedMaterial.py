from argparse import ArgumentParser
from hashlib import sha256
from math import isfinite
from pathlib import Path
import json
import os

PREVIOUS = "9314fb1c0192ec5fbfb460bbaaed1b6ac2c89aa5e1097065eade06bb0f4e27d5"
MODE_CHANGED = {"AlAll": 0.011375, "SteelAll": 0.009875}
SCHEMA = "kit.sw2026.assigned-material-persistence.v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return sha256(data).hexdigest()


def read_exact(path, expected):
    data = path.read_bytes()
    require(sha(data) == expected, "material persistence input differs: " + path.name)
    return data


def freeze(cold_root, output):
    checked = json.loads(read_exact(cold_root / "Job.json", PREVIOUS))
    files = {name: read_exact(cold_root / "Tools" / name, expected)
             for name, expected in checked["tools_sha256"].items()}
    command = Path(__file__).resolve()
    files[command.name] = command.read_bytes()
    (output / "Tools").mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / "Tools" / name).write_bytes(data)
    plan = {"schema": SCHEMA, "cold_job_sha256": PREVIOUS, "cold_root": checked["guest_root"],
            "edited_depth_m": MODE_CHANGED, "tools_sha256": {k: sha(v) for k, v in files.items()}}
    data = json.dumps(plan, indent=2, sort_keys=True, allow_nan=False).encode("utf-8") + b"\n"
    (output / "Job.json").write_bytes(data)
    return {"job_sha256": sha(data), "tools": len(files), "native_processes": 0}


def read_plan(path, pin):
    require(os.name == "nt" and path.is_absolute() and path.drive == "C:",
            "material persistence requires the root Windows oracle")
    plan = json.loads(read_exact(path, pin))
    require(path.name == "Job.json" and plan["schema"] == SCHEMA and plan["cold_job_sha256"] == PREVIOUS
            and plan["edited_depth_m"] == MODE_CHANGED and plan["cold_root"] == r"C:\KitAssignedMaterialProbe01",
            "persistence method does not bind the two disclosed cold cases")
    output = path.parent
    declared = plan["tools_sha256"]
    require({p.name for p in (output / "Tools").iterdir() if p.is_file()} == set(declared),
            "material persistence tool inventory differs")
    for name, expected in declared.items():
        require(Path(name).name == name, "material persistence tool locator escapes packet")
        read_exact(output / "Tools" / name, expected)
    return plan


def edited_expectations(row, depth):
    sketch, feature = row["feature_names"]
    drivers = row["drivers_m"]
    width, height = (drivers[f"D{index}@{sketch}"] for index in (1, 2))
    parameter = f"D1@{feature}"
    require(isfinite(depth) and 0 < depth <= 0.25 and depth != drivers[parameter],
            "probe driving edit must change the positive authored depth")
    geometry = {"volume": width * height * depth, "area": 2 * (width * height + width * depth + height * depth),
                "com": [*row["geometry"]["com"][:2], depth / 2]}
    edited = row | {"geometry": geometry, "drivers_m": drivers | {parameter: depth}}
    return parameter, edited


def observe(output, row, input_path, input_pin, depth, *, edit):
    import Swapp
    from AuthorCurves import Recorder, digest
    from AuthorRectangleAnchors import ORACLE, RectangleAuthor
    from OracleIdentity import application_identity
    from RunAssignedMaterialProbe import snapshot

    parameter, changed = edited_expectations(row, depth)
    output.mkdir(parents=True, exist_ok=False)
    rec = Recorder(output / "Record.json", {"phase": "EditAndSave" if edit else "FreshReopen"})
    report = {"passed": False, "identity": None, "states": {}, "save": None}
    rec.data["result"] = report
    controller = author = None

    def rebuild():
        require(author.get(author.model, "ForceRebuild3", False)
                and author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount") == 0,
                "material persistence rebuild failed or warned")

    def measure(key, active):
        state = snapshot(author, active, key)
        require(state["matches_requested_identity"] and state["matches_requested_density"]
                and state["matches_requested_mass"],
                "named material or physical mass did not survive " + key)
        report["states"][key] = state

    require(digest(input_path) == input_pin, "exact material persistence candidate changed before native open")
    with Swapp.Dismisser() as dialogs:
        try:
            require(not Swapp.application_pids(), "the named oracle must already be idle")
            controller = rec.call("start fresh material persistence oracle", Swapp.Sw)
            identity = application_identity(controller.app)
            report["identity"] = identity
            require(identity["sha256"] == ORACLE and identity["version_matches"]
                    and controller.revision == "34.5.2", "material persistence executable changed")
            author = RectangleAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call("open exact material persistence input",
                                                       controller.open, input_path, read_only=not edit)
            report["open_errors_warnings"] = [errors, warnings]
            require(author.model is not None and errors == warnings == 0
                    and Path(author.get(author.model, "GetPathName")).samefile(input_path),
                    "material persistence file failed to open cleanly at its exact locator")
            if edit:
                measure("cold", row)
                rebuild()
                measure("rebuilt", row)
                author.edit(parameter, depth)
                rebuild()
                measure("edited", changed)
                target_dir = output / "Published"
                target_dir.mkdir(exist_ok=False)
                target = target_dir / input_path.name
                require(not target.exists(), "native persistence target already exists")
                author.get(author.model, "SetSaveFlag")
                status = rec.call("save edited material candidate separately", controller.save_as, author.model, target)
                require(status == (True, 0, 0) and target.is_file() and target.stat().st_size > 0
                        and Path(author.get(author.model, "GetPathName")).samefile(target),
                        "material persistence save failed or warned")
                measure("after_save", changed)
                report["save"] = {"path": str(target), "sha256": digest(target),
                                  "bytes": target.stat().st_size, "diagnostics": list(status)}
            else:
                measure("fresh_reopen", changed)
                rebuild()
                measure("fresh_rebuild", changed)
            report["passed"] = True
        except Exception as error:
            rec.failure(error)
            report["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                    require(not Swapp.application_pids(), "material persistence process did not exit")
                except Exception as error:
                    rec.failure(error, cleanup=True)
                report["controller_diagnostics"] = controller.diagnostics
    report.update(dialogs=dialogs.log, numeric_checks=len(rec.data["checks"]),
                  input_after_sha256=digest(input_path))
    report["passed"] = bool(report["passed"] and report["input_after_sha256"] == input_pin
                            and not dialogs.log and not rec.data["cleanup_errors"]
                            and not report["controller_diagnostics"])
    rec.data["passed"] = report["passed"]
    rec.flush()
    return report | {"record_sha256": digest(rec.path)}


def run(path, pin):
    plan = read_plan(path, pin)

    from AuthorCurves import digest, write_json
    from AuthorRectangleAnchors import control
    from RunAssignedMaterialProbe import read_job

    cold, original, seed = read_job(Path(plan["cold_root"]) / "Job.json", PREVIOUS)
    output = path.parent / "Inspection"
    output.mkdir(exist_ok=False)
    report = {"schema": SCHEMA, "job_sha256": pin, "cold_job_sha256": PREVIOUS,
              "research_only": True, "heldout_credit": 0, "cases": {}}
    result = output / "Result.json"
    try:
        report["before"] = control(output, "ControlBefore", seed)
        if report["before"]["passed"]:
            for name, depth in plan["edited_depth_m"].items():
                row = original["cases"][name]
                require(row["mode"] == "all", "paired all-owner cases are required")
                candidate = cold / "Models" / (name + ".SLDPRT")
                edit = observe(output / name / "Edit", row, candidate, row["sha256"], depth, edit=True)
                stages = {"edit": edit}
                report["cases"][name] = stages
                if edit["passed"]:
                    save = edit["save"]
                    stages["reopen"] = observe(output / name / "Reopen", row, Path(save["path"]),
                                               save["sha256"], depth, edit=False)
                write_json(result, report)
    finally:
        report["after"] = control(output, "ControlAfter", seed)
        cases = [row for stages in report["cases"].values() for row in stages.values()]
        rows = (report.get("before", {}), report["after"], *cases)
        identities = (row.get("identity") or row.get("oracle_identity") for row in rows)
        report["distinct_processes"] = len({(i["process_id"], i["process_creation_filetime"]) for i in identities if i})
        report["controls_healthy"] = all(report.get(key, {}).get("passed", False) for key in ("before", "after"))
        report["passed"] = len(rows) == report["distinct_processes"] == 6 and all(row["passed"] for row in rows)
        read_plan(path, pin)
        read_job(Path(plan["cold_root"]) / "Job.json", PREVIOUS)
        write_json(result, report)
    return {"passed": report["passed"], "controls_healthy": report["controls_healthy"],
            "native_processes": report["distinct_processes"], "result_sha256": digest(result)}


if __name__ == "__main__":
    cli = ArgumentParser()
    modes = cli.add_subparsers(dest="mode", required=True)
    prep = modes.add_parser("freeze")
    prep.add_argument("cold_root", type=Path)
    prep.add_argument("output", type=Path)
    windows = modes.add_parser("run")
    windows.add_argument("job", type=Path)
    windows.add_argument("pin")
    args = cli.parse_args()
    result = freeze(args.cold_root, args.output) if args.mode == "freeze" else run(args.job, args.pin)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(not result.get("passed", True))
