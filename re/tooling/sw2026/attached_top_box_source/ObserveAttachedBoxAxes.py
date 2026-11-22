from argparse import ArgumentParser
from json import dumps, loads
from math import isfinite, sqrt
from pathlib import Path, PureWindowsPath
from platform import machine, python_version
from re import fullmatch
from shutil import copyfile
from time import time
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import RunAttachedTopBoxSources as box
from AuthorCurves import application_pids, digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control


SCHEMA = "kit.sw2026.attached-box-axes-native.v1"
NATIVE = PureWindowsPath(r"C:\KitAttachedBoxAxes01\F14c.SLDPRT")
SOURCE = "25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb"
AXES = {
    "X-axis": ((1.0, 0.0, 0.0), ("Top Plane", "Front Plane")),
    "Y-axis": ((0.0, 1.0, 0.0), ("Front Plane", "Right Plane")),
    "Z-axis": ((0.0, 0.0, 1.0), ("Right Plane", "Top Plane")),
}
TOOLS = {
    *box.TOOLS,
    "AuthorPartProperties.py",
    "ObserveAttachedBoxAxes.py",
}


def checked(folder, name, expected):
    path = folder / name
    require(path.is_file() and not path.is_symlink() and digest(path) == expected,
            f"attached axis packet identity differs at {name}")
    return path


def read_job(path, expected):
    folder = path.parent
    job = loads(checked(folder, path.name, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["native_path"] == str(NATIVE)
            and job["oracle_sha256"] == ORACLE
            and job["oracle_version"] == box.ORACLE_VERSION
            and job["source_sha256"] == SOURCE and set(job["tools"]) == TOOLS
            and job["control_sha256"] == CONTROL,
            "expected the exact disclosed attached box axis packet")
    require(Path(__file__).resolve().parent == folder / "Tools",
            "use the observer in the verified packet")
    for name, checksum in job["tools"].items():
        checked(folder / "Tools", name, checksum)
    for name, key in (("Control.SLDPRT", "control_sha256"),
                      ("F14c.SLDPRT", "candidate_sha256"),
                      ("Build.json", "build_sha256")):
        checked(folder, name, job[key])
    require(tuple(job["original_m"]) == box.ORIGINAL_F14C
            and tuple(job["edit_m"]) == box.DISCLOSED_EDITS,
            "the observation must use the independently disclosed dimensions")
    return job


def check_axis(author, name, expected):
    direction, parent_names = expected
    feature = author.get(author.model, "FeatureByName", name)
    require(feature is not None and author.get(feature, "GetTypeName2") == "RefAxis",
            f"{name} is missing from the live native reference feature tree")
    parents = author.get(feature, "GetParents") or ()
    observed_parents = [str(author.get(parent, "Name")) for parent in parents]
    require(len(observed_parents) == 2 and set(observed_parents) == set(parent_names)
            and all(author.get(parent, "GetTypeName2") == "RefPlane" for parent in parents),
            f"{name} lost its two independently owned datum planes")
    axis = author.get(feature, "GetSpecificFeature2")
    require(axis is not None, f"{name} has no live axis geometry object")
    words = tuple(float(word) for word in author.get(axis, "GetRefAxisParams"))
    require(len(words) == 6 and all(isfinite(word) for word in words), f"{name} has invalid endpoints")
    delta = tuple(words[index + 3] - words[index] for index in range(3))
    extent = sqrt(sum(word * word for word in delta))
    require(extent > 1e-9, f"{name} is degenerate")
    normalized = tuple(word / extent for word in delta)
    author.rec.close_number(name + " direction", sum(a * b for a, b in zip(normalized, direction)), 1.0)
    for index, word in enumerate(direction):
        if not word:
            author.rec.close_number(name + " origin first", words[index], 0.0, absolute=1e-10)
            author.rec.close_number(name + " origin second", words[index + 3], 0.0, absolute=1e-10)
    require(author.get(feature, "Select2", False, 0), f"{name} is not selectable")
    author.get(author.model, "ClearSelection2", True)
    return {"parents": observed_parents, "endpoints_m": [words[:3], words[3:]],
            "unit": normalized, "selectable": True}


def write_result(folder, result):
    write_json(folder / "Result.json", result)


def run(packet, expected, trial):
    require(os.name == "nt", "the native observer runs in the Windows guest")
    import pythoncom

    require(pythoncom.IID_IDispatch is not None,
            "the native observer needs its registered COM runtime")
    job = read_job(packet, expected)
    require(not application_pids(), "the oracle must be idle before the bracket")
    require(fullmatch(r"Trial[0-9]{2}", trial), "choose a fresh exact native trial")
    root = Path(NATIVE).parent
    if not root.exists():
        root.mkdir()
        for name in (NATIVE.name, "Control.SLDPRT"):
            copyfile(packet.parent / name, root / name)
    candidate = checked(root, NATIVE.name, job["candidate_sha256"])
    control_file = checked(root, "Control.SLDPRT", job["control_sha256"])
    folder = root / trial
    folder.mkdir(exist_ok=False)
    result = {"schema": SCHEMA, "job_sha256": expected, "candidate_sha256": digest(candidate),
              "oracle_build": job["oracle_version"], "oracle_sha256": ORACLE,
              "python_version": python_version(), "python_machine": machine(),
              "native_destination": str(NATIVE), "passed": False, "phases": {},
              "started_at": time()}
    write_result(folder, result)
    original_snapshot = box.snapshot

    def observe(author, case, state):
        measured = original_snapshot(author, case, state)
        measured["axes"] = {name: check_axis(author, name, intent)
                            for name, intent in AXES.items()}
        return measured

    case = {name: job[name] for name in ("source_sha256", "original_m", "edit_m", "source_text")}
    box.snapshot = observe
    phases = result["phases"]
    try:
        phases["before"] = control(folder, "ControlBefore", control_file)
        write_result(folder, result)
        if phases["before"]["passed"]:
            phases["generated"] = box.phase(folder, case, "Author", generated_input=candidate)
            write_result(folder, result)
            if phases["generated"]["passed"]:
                phases["reopen"] = box.phase(folder, case, "Reopen", phases["generated"])
                write_result(folder, result)
    finally:
        box.snapshot = original_snapshot
        phases["after"] = control(folder, "ControlAfter", control_file)
        result["finished_at"] = time()
        write_result(folder, result)
    require(digest(candidate) == job["candidate_sha256"], "native measurement altered the original candidate")
    identities = []
    for phase in phases.values():
        identity = phase.get("oracle_identity")
        if identity is not None:
            require(identity["sha256"] == ORACLE and identity["file_version"] == box.ORACLE_VERSION,
                    "native phase reported a different executable")
            identities.append((identity["process_id"], identity["process_creation_filetime"]))
    result["controls_healthy"] = phases["before"]["passed"] and phases["after"]["passed"]
    result["distinct_processes"] = len(set(identities))
    result["passed"] = (
        tuple(phases) == ("before", "generated", "reopen", "after")
        and len(identities) == result["distinct_processes"] == 4
        and all(left[1] < right[1] for left, right in zip(identities, identities[1:]))
        and all(row["passed"] for row in phases.values())
    )
    result["candidate_unchanged"] = True
    read_job(packet, expected)
    write_result(folder, result)
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("sha256")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--trial", default="Trial01")
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.verify_only:
        print(dumps({"native_destination": read_job(packet, args.sha256)["native_path"]}))
    else:
        output = run(packet, args.sha256, args.trial)
        print(dumps({key: output[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
        raise SystemExit(0 if output["passed"] else 3)
