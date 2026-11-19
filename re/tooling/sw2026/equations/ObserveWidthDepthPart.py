from argparse import ArgumentParser
import json
import os
from pathlib import Path

import AuthorEquationSources01 as equations
from AuthorCurves import Recorder, digest, require


class PlainPartObserver(equations.EquationAuthor):
    def read_equations(self, case, edited):
        require(self.eq(self.manager(), "GetCount", 1) == 0, "the plain control owns an equation")
        return []

    def source_snapshot(self, case, edited):
        fixed_depth = {**case, "width_mm": case["edit_width_mm"]} if edited else case
        return super().source_snapshot(fixed_depth, False)

    def edit_source(self, case):
        self.edit(equations.PARAMETERS[0], case["edit_width_mm"] / 1000)


def load_job(path, expected):
    require(digest(path) == expected, "the frozen width/depth job changed")
    job = json.loads(path.read_bytes())
    require(
        job["schema"] == "kit.sw2026.width-depth-local-reference.v1"
        and set(job["cases"]) == {"ControlBefore", "Alpha", "Beta", "ControlAfter"},
        "the declared width/depth cohort differs",
    )
    for name, checksum in job["files"].items():
        relative = Path(name)
        require(
            not relative.is_absolute() and ".." not in relative.parts
            and digest(path.parent / relative) == checksum,
            "a frozen input or tool changed",
        )
    require(
        job["files"]["ApiMetadata01.json"] == equations.METADATA,
        "the registered equation API metadata changed",
    )
    require(
        Path(__file__).resolve().parent == path.resolve().parent / "Tools",
        "run the observer from the verified packet",
    )
    for role, entry in job["cases"].items():
        require(entry["path"] in job["files"], "undeclared native part input")
        if "plain_control" in entry:
            require(
                type(entry["plain_control"]) is bool and role in ("Alpha", "Beta"),
                "the plain-control lane must use a declared candidate role",
            )
    return job


def bind_names(specification):
    equations.SKETCH = specification["sketch_name"]
    equations.BOSS = specification["boss_name"]
    equations.PARAMETERS = (
        f"D1@{equations.SKETCH}",
        f"D2@{equations.SKETCH}",
        f"D1@{equations.BOSS}",
    )


def inspect(path, job, role, reopen=False, prior=None):
    import Swapp
    from OracleIdentity import application_identity

    root = path.parent
    spec = job["cases"][role]
    bind_names(spec)
    edit = role in ("Alpha", "Beta") and not reopen
    phase = role + "Reopen" if reopen else role
    saved_path = root / "Inspection" / role / "Edited.SLDPRT"
    input_path = saved_path if reopen else root / spec["path"]
    checksum = digest(input_path)
    if reopen:
        require(checksum == prior["saved_sha256"], "the saved derivative changed")
    output = root / "Inspection" / phase
    output.mkdir(exist_ok=False)
    record = Recorder(output / "Record.json", {"role": phase, "input_sha256": checksum})
    case = spec["case"]
    metadata = json.loads((root / "ApiMetadata01.json").read_bytes())
    plain_control = spec.get("plain_control", False)
    result = {
        "open_status": None, "passed": False, "input_sha256": checksum,
        "plain_control": plain_control,
    }
    controller = None
    with Swapp.Dismisser() as dialogs:
        try:
            Swapp.sweep()
            controller = record.call("start fresh SOLIDWORKS", Swapp.Sw)
            identity = record.call("verify exact native build", application_identity, controller.app)
            require(
                identity["sha256"] == equations.ORACLE
                and identity["version_matches"]
                and identity["file_version"] == "34.5.2.0604",
                "the SOLIDWORKS build differs",
            )
            result["oracle_identity"] = identity
            record.data["oracle_identity"] = identity
            record.flush()
            observer_kind = PlainPartObserver if plain_control else equations.EquationAuthor
            author = observer_kind(controller.app, record, Swapp, metadata)
            model, error, warning = record.call(
                "open the frozen native part",
                controller.open, input_path, read_only=not edit,
            )
            result["open_status"] = [error, warning]
            require(
                model is not None and error == warning == 0
                and Path(author.get(model, "GetPathName")).samefile(input_path),
                "the candidate did not open cleanly at the declared path",
            )
            author.model = model
            part = author.typed(model, "PartDoc")
            result["body_count_at_open"] = len(author.get(part, "GetBodies2", 0, False) or ())
            require(result["body_count_at_open"] == 1, "the open has no unique native solid")
            result["original"] = author.source_snapshot(case, reopen)
            if reopen:
                equations.same_structure(result["original"], prior["edited"])
            if edit:
                author.edit_source(case)
                result["edited"] = author.source_snapshot(case, True)
                equations.same_structure(result["edited"], result["original"])
                require(not saved_path.exists(), "the edited output path is already occupied")
                status = record.call("save the edited derivative", controller.save_as, model, saved_path)
                result["save_status"] = list(status)
                require(tuple(status) == (True, 0, 0), "native save failed or warned")
                result["saved_sha256"] = digest(saved_path)
            result["passed"] = True
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    record.failure(error, cleanup=True)
    result.update(
        numeric_checks=len(record.data["checks"]),
        first_failure=record.data["first_failure"],
        input_unchanged=digest(input_path) == checksum,
        dialogs=dialogs.log,
    )
    result["passed"] = bool(
        result["passed"] and result["input_unchanged"] and not result["dialogs"]
        and not result.get("controller_diagnostics") and not record.data["cleanup_errors"]
    )
    record.data.update(result=result, passed=result["passed"])
    record.flush()
    equations.write_new(output / "Result.json", result)
    return result


def run(path, expected, job):
    equations.guest_only(job)
    (path.parent / "Inspection").mkdir(exist_ok=False)
    phases = {"ControlBefore": inspect(path, job, "ControlBefore")}
    try:
        if phases["ControlBefore"]["passed"]:
            for role in ("Alpha", "Beta"):
                phases[role] = inspect(path, job, role)
                if not phases[role]["passed"]:
                    break
                reopen_role = role + "Reopen"
                phases[reopen_role] = inspect(path, job, role, reopen=True, prior=phases[role])
                if not phases[reopen_role]["passed"]:
                    break
    finally:
        phases["ControlAfter"] = inspect(path, job, "ControlAfter")
    load_job(path, expected)
    identities = {
        (data["oracle_identity"]["process_id"], data["oracle_identity"]["process_creation_filetime"])
        for data in phases.values() if "oracle_identity" in data
    }
    result = {
        "job_sha256": expected,
        "controls_healthy": phases["ControlBefore"]["passed"] and phases["ControlAfter"]["passed"],
        "distinct_native_processes": len(identities),
        "phases": phases,
        "passed": len(identities) == len(phases) == 6 and all(item["passed"] for item in phases.values()),
    }
    equations.write_new(path.parent / "Inspection" / "Summary.json", result)
    return result["passed"]


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run", "control-after"))
    parser.add_argument("job", type=Path)
    parser.add_argument("sha256")
    args = parser.parse_args()
    job = load_job(args.job, args.sha256)
    if args.mode == "control-after":
        equations.guest_only(job)
        (args.job.parent / "Inspection").mkdir(exist_ok=False)
        passed = inspect(args.job, job, "ControlAfter")["passed"]
    else:
        passed = args.mode == "verify" or run(args.job, args.sha256, job)
    print(json.dumps({"passed": passed}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
