from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import sys
from traceback import format_exc


SOURCE_ROOT = PureWindowsPath(r"C:\KitEllipseBlindBossHoldout01")
LOCK_SHA = "e152ceab9e1738d85058e6bc85cb46422b64cf92104b3ad0ba4726bee172a43e"
SOURCE_MODULES = ("EllipseModel.py", "EllipsePacket.py", "RunEllipseSources.py")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pinned(path, pin):
    require(path.is_file() and not path.is_symlink() and path.resolve() == path, "source custody path differs")
    data = path.read_bytes()
    require(sha256(data).hexdigest() == pin, "source custody digest differs")
    return data


def guard(event, args):
    if event.startswith(("socket.", "ctypes.", "winreg.", "subprocess.")) or event in (
        "os.startfile", "os.startfile/2", "os.system", "os.exec", "os.posix_spawn",
    ):
        raise PermissionError("source custody process cannot invoke an external runtime")
    if event == "open":
        _, mode, flags = args
        if (mode and any(letter in mode for letter in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR):
            raise PermissionError("source custody process is read-only")


def read(public):
    require(os.name == "nt", "protected source custody is Windows-only")
    sys.addaudithook(guard)
    sealed = json.loads(pinned(public, LOCK_SHA))
    source = Path(SOURCE_ROOT)
    manifest = source / "Packet/SourceJob.json"
    summary = json.loads(pinned(manifest, sealed["source_job_sha256"]))
    tool = manifest.parent / "Tool"
    for name in SOURCE_MODULES:
        pinned(tool / name, summary["files"][f"Tool/{name}"]["sha256"])
    sys.path.insert(0, str(tool))
    from EllipsePacket import verify
    from RunEllipseSources import checked_lock, exact, paths, reconcile

    job, cases, predictions = verify(manifest, sealed["source_job_sha256"], permit_private=True)
    capture = source / "Capture"
    lock = checked_lock(job, sealed["source_job_sha256"], capture, sealed["source_lock_sha256"])
    require(all(lock[key] == sealed[key] for key in (
        "revision", "tree", "oracle_build", "oracle_sha256", "spec_sha256", "prediction_sha256",
        "registered_api_sha256", "distinct_processes", "writer_output_count", "heldout_writer_acceptance", "finished_at",
    )) and all(job[key] == sealed[key] for key in ("disclosed_job_sha256", "disclosed_lock_sha256")),
        "locked source does not reproduce its published authority")
    controls, lives = {}, []

    def lifetime(record):
        identity = record["oracle_identity"]
        require(exact(identity) and identity["process_id"] > 0 and identity["process_creation_filetime"] > 0,
                "locked observation lacks exact native process identity")
        lives.append([identity["process_id"], identity["process_creation_filetime"]])

    pinned(capture / "RegisteredApi.json", sealed["registered_api_sha256"])
    require(lock["controls"].keys() == sealed["controls"].keys(), "source control inventory differs")
    for key, row in lock["controls"].items():
        pin = sealed["controls"][key]
        record = json.loads(pinned(capture / key / "Record.json", pin))
        require(row["phase_sha256"] == pin and row["exit_code"] == 0 and row["passed"] is record["passed"] is True,
                "source control failed")
        lifetime(record)
        controls[key] = pin

    slots = []
    for index, (case, prediction, row, published) in enumerate(zip(cases, predictions, lock["sources"], sealed["slots"], strict=True)):
        folder, initial, edited = paths(capture, index, case)
        require(published["slot"] == folder.name and row["original_sha256"] == published["original_sha256"]
                and row["edited_sha256"] == published["edited_sha256"] != published["original_sha256"]
                and [phase["phase_sha256"] for phase in row["phases"]] == published["phases"],
                "source artifacts or phase bindings differ")
        pinned(initial, published["original_sha256"])
        pinned(edited, published["edited_sha256"])
        records = []
        pins = (None, published["original_sha256"], published["edited_sha256"])
        for phase, incoming in zip(row["phases"], pins, strict=True):
            name = phase["phase"]
            artifact = published["original_sha256"] if name == "author" else published["edited_sha256"]
            record = json.loads(pinned(folder / name / "Record.json", phase["phase_sha256"]))
            require(phase["job_sha256"] == sealed["source_job_sha256"] and phase["slot"] == index
                    and phase["source_sha256"] == incoming and phase["artifact_sha256"] == artifact
                    and phase["exit_code"] == 0 and phase["passed"] is record["passed"] is True
                    and record["job"] == {"phase": name, "source_sha256": incoming}
                    and record["artifact_sha256"] == artifact and record["writer_output_count"] == 0
                    and record["source_immutable"] and record["first_failure"] is None and not record["cleanup_errors"]
                    and not record["dialogs"] and not record["controller_diagnostics"]
                    and len(record["checks"]) == phase["checks"] and all(check["passed"] for check in record["checks"]),
                    "locked source lifecycle observation differs")
            if incoming is not None:
                require(record["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                        and record["cold"] == {"solids": 1, "diagnostics": 0}, "locked source open was not clean")
            if name != "edited-reopen":
                require(record["save_status"] == [True, 0, 0], "locked source save was not clean")
            lifetime(record)
            records.append(record)
        lifecycle = reconcile(initial, edited, records)
        require(lifecycle == {key: row[key] for key in lifecycle} and lifecycle["tree_rows"] == 25,
                "locked source ownership or lifecycle differs")
        slots.append({"case": case, "prediction": prediction, "locked": published,
                      "snapshots": [records[0]["authored"], records[1]["reopened"],
                                    records[1]["edited"], records[2]["reopened"]],
                      "driver_edit": records[1]["driver_edit"], "checks": sum(len(row["checks"]) for row in records)})
    require(len(lives) == len({tuple(life) for life in lives}) == 10, "source process lifetimes are not independent")
    return {"slots": slots, "controls": controls, "lifetimes": lives}


def main():
    cli = ArgumentParser()
    cli.add_argument("public_lock", type=Path)
    request = cli.parse_args()
    try:
        result = read(request.public_lock)
    except Exception:
        if os.name == "nt":
            print(format_exc(), file=sys.stderr)
        return 2
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
