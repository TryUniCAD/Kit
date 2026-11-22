from argparse import ArgumentParser
from base64 import b64decode
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[1] / "edge_fillet_source"))

from EllipseModel import CASES, SCHEMA as INTENT_SCHEMA, predict, require, validate
from EllipsePacket import ASSETS, BUILD, CONTROLS, FAMILY, ORACLE, SHARE, TOOLS, digest, encode, pinned_json, put, sha, valid_hash

SCHEMA = "kit.sw2026.cold-ellipse-prototype.v1"
NAME = "EllipseColdPrototype01"
GUEST = PureWindowsPath(r"C:\KitEllipseColdPrototype01")
TOOLS_COLD = TOOLS | {FAMILY: (*TOOLS[FAMILY], "EllipseSeamPacket.py", "EllipseSeamObserve.py",
                               "EllipseSeamAuthor.py", "ColdEllipsePacket.py", "RunColdEllipseProbe.py")}
TRIAL = "Trial.json"
EPOCH = 1795516920
SOURCE_TERMINALS = {
    "EllipseSeamDiscriminator01": "24835a708644209a1d8fb73fa17b36f85d471c7308b38d22d6a22f75870cb39d",
    "EllipseSeamNoUpdate01": "efbd584eca6cafdd9b715b1a03b26db6a0f146ab51c850681dfee2268cfc3cc8",
}
REQUESTED_OBSERVER = {"major_station_seed": True, "post_rebuild_phase": "observe"}


def candidate_path(case):
    return "Candidates/" + case["name"] + ".SLDPRT"


def closure(cases):
    return ({f"Tool/{name}" for names in TOOLS_COLD.values() for name in names} | set(CONTROLS)
            | {candidate_path(case) for case in cases} | {"ReferenceTree.json"})


def verify(path, pin):
    job = pinned_json(path, pin)
    folder = path.resolve().parent
    cases = validate(job["spec"], "disclosed")
    require(path.name == TRIAL and job["schema"] == SCHEMA and job["construction_scope"] == REQUESTED_OBSERVER
            and job["native_build"] == BUILD and job["oracle_sha256"] == ORACLE
            and valid_hash(job["revision"], 40) and valid_hash(job["src_tree"], 40)
            and job["guest_root"] == str(GUEST) and job["source_terminals"] == SOURCE_TERMINALS
            and job["guarded_writer_processes"] == 4 and job["runtime_accesses"] == job["heldout_credit"] == 0
            and cases == list(CASES), "prototype plan or disclosure custody differs")
    files = job["files"]
    require(set(files) == closure(cases)
            and {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} == set(files) | {TRIAL}
            and all(files[name]["sha256"] == checksum for name, checksum in CONTROLS.items()),
            "prototype frozen file inventory or independent controls differ")
    for name, entry in files.items():
        item = folder / name
        require(item.is_file() and not item.is_symlink() and item.resolve() == item
                and item.stat().st_size == entry["bytes"] and sha(item) == entry["sha256"],
                f"prototype packet file changed: {name}")
    reference = json.loads((folder / "ReferenceTree.json").read_bytes())
    require(len(reference["tree"]) == 25 and reference["configurations"] == ["Default"]
            and reference["parents"] == ["EllipseProfile", "Front Plane"] and reference["children"] == ["EllipseProfile"],
            "same ordinary native reference tree or support differs")
    for case, entry in zip(cases, job["candidates"], strict=True):
        relative = candidate_path(case)
        proof = entry["proof"]
        require(entry["path"] == relative and proof["locator"] == str(GUEST / "Packet" / relative)
                and proof["archive_sha256"] == files[relative]["sha256"] and proof["bytes"] == files[relative]["bytes"]
                and len(proof["streams"]) == 10 and len(proof["ellipse"]["linked_replays"]) == 2
                and proof["runtime_accesses"] == 0, "candidate is outside the guarded neutral freeze")
    return job, cases, reference


def stage(path, pin):
    require(os.name == "nt" and PureWindowsPath(path.resolve()).is_relative_to(SHARE),
            "stage the disclosed prototype from the managed share")
    job, _, _ = verify(path, pin)
    root = Path(GUEST)
    require(root.resolve() == root and not root.exists(), "prototype guest root is occupied")
    destination = root / "Packet"
    destination.mkdir(parents=True)
    for name in sorted((*job["files"], TRIAL)):
        item = destination / name
        item.parent.mkdir(exist_ok=True)
        put(item, (path.parent / name).read_bytes())
    verify(destination / TRIAL, pin)


def measured_pair(shared):
    from math import dist

    references, evidence = [], {}
    for name, pin in SOURCE_TERMINALS.items():
        expected_close = name == "EllipseSeamDiscriminator01"
        capture = shared / name / "DisclosedCapture"
        result = pinned_json(capture / "SeamResult.json", pin)
        require(result["passed"] and result["idle_after"] and result["inputs_unchanged"]
                and result.get("close_updates", True) is expected_close
                and result["distinct_processes"] == result["fresh_processes"] == 8
                and result["oracle_build"] == BUILD and result["oracle_sha256"] == ORACLE
                and len(result["controls"]) == 4 and all(item["passed"] for item in result["controls"].values())
                and result["writer_output_count"] == 0, "paired source does not prove the disclosed close observation")
        phase = result["phases"]["author-boss"]
        record = pinned_json(capture / "author-boss/Record.json", phase["record_sha256"])
        require(phase["passed"] and record["passed"] and record.get("close_updates", True) is expected_close,
                "selected disclosed author record disagrees with its root terminal")
        shape = record["shape"]
        references.append({"tree": shape["tree"], "configurations": shape["configurations"],
                           "parents": shape["definition"]["parents"], "children": shape["definition"]["children"]})
        states = {entry["stage"]: entry for entry in record["seam_stages"]}
        seam = []
        for label in ("draw_open", "sketch_closed", "boss_created", "before_save"):
            row = states[label]
            a, b = (entry["point"] for entry in row["endpoints"].values() if entry["status"] == "observed")
            require(a == b and a["id"] != row["ellipse"]["point_ids"]["Major"],
                    "recorded endpoint is not the distinct shared seam")
            seam.append(a)
        require(len({tuple(row["id"]) for row in seam}) == 1, "source seam ownership moved to another point")
        stations = [row["xyz_m"] for row in seam]
        major = shape["profile"]["points_m"]["Major"]
        expected_major = [True, not expected_close, not expected_close, False]
        require([dist(point, major) < 1e-14 for point in stations] == expected_major,
                "source seam transition does not distinguish no-update close from native rebuild")
        evidence[name] = {"record_sha256": phase["record_sha256"], "live_point_id": seam[0]["id"],
                          "major_station_matches": expected_major, "rebuilt_station_m": stations[-1]}
    require(references[0] == references[1] and len(references[0]["tree"]) == 25,
            "the paired native source trees differ")
    return references[0], evidence


def neutral_wire(case, index):
    expected = predict(case)
    model = {name: case[name] for name in ("name", "center_mm", "radii_mm", "depth_mm")}
    model["major_xy"] = expected["unit_axes"][0][:2]
    return encode({"model": model, "locator": str(GUEST / "Packet" / candidate_path(case)), "epoch": EPOCH + index * 61})


def compiled(wire):
    process = subprocess.run([sys.executable, "-I", "-B", str(HERE.with_name("CompileColdEllipse.py")), "--deliver"],
                             input=wire, capture_output=True, timeout=90, check=False)
    require(process.returncode == 0 and not process.stderr, process.stderr.decode())
    return process.stdout


def freeze(output):
    require(output.is_absolute() and output.name == "Packet" and output.parent.name == NAME
            and not output.exists() and not output.resolve().is_relative_to(ROOT), "select the unused disclosed prototype")

    def git(*args):
        return subprocess.check_output(("git", "-C", str(ROOT), *args))

    revision = git("rev-parse", "HEAD").decode().strip()
    require(not git("status", "--porcelain", "--untracked-files=no"), "freeze the committed generator and observer")
    reference, paired = measured_pair(output.parents[1])
    assets = {f"Tool/{name}": git("show", f"{revision}:{folder}/{name}") for folder, names in TOOLS_COLD.items() for name in names}
    assets.update({name: git("show", f"{revision}:{ASSETS}/{name}") for name in CONTROLS})
    assets["ReferenceTree.json"] = encode(reference)
    candidates = []
    for index, case in enumerate(CASES):
        wire = neutral_wire(case, index)
        first, second = compiled(wire), compiled(wire)
        require(first == second, "two independent neutral ellipse workers produced different artifacts")
        proof = json.loads(first)
        data = b64decode(proof.pop("model_base64"), validate=True)
        require(proof["input_sha256"] == digest(wire) and proof["archive_sha256"] == digest(data)
                and proof["runtime_accesses"] == 0 and proof["bytes"] == len(data),
                "guarded ellipse worker receipts are unbound")
        relative = candidate_path(case)
        assets[relative] = data
        candidates.append({"path": relative, "proof": proof})
    require(len({row["proof"]["archive_sha256"] for row in candidates}) == len(CASES),
            "the distinct signed neutral ellipses must produce distinct archives")
    job = {"schema": SCHEMA, "construction_scope": REQUESTED_OBSERVER, "revision": revision,
           "src_tree": git("rev-parse", f"{revision}:src").decode().strip(), "native_build": BUILD, "oracle_sha256": ORACLE,
           "guest_root": str(GUEST), "source_terminals": SOURCE_TERMINALS, "paired_source": paired,
           "spec": {"schema": INTENT_SCHEMA, "cohort": "disclosed", "cases": list(CASES)},
           "guarded_writer_processes": 4, "runtime_accesses": 0, "heldout_credit": 0,
           "candidates": candidates, "files": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in assets.items()}}
    output.mkdir(parents=True)
    for name, data in assets.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        put(path, data)
    put(output / TRIAL, encode(job))
    pin = sha(output / TRIAL)
    verify(output / TRIAL, pin)
    return {"trial_sha256": pin, "revision": revision, "candidates": candidates, "files": len(assets)}


if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("--output", type=Path, required=True)
    print(json.dumps(freeze(args.parse_args().output), sort_keys=True))
