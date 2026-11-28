from base64 import b64decode
from json import dumps, loads
from pathlib import Path, PureWindowsPath
import os
import subprocess
import sys

from RunPairCandidates import METHODS, PROTECTED_SOURCE, digest, method, pinned, require, write_new


HERE = Path(__file__).resolve().parent
SOURCE_REVISION = "9e939d42ca5eaa9e71c1c253c255010c9ef9c99e"
EPOCH = 1795332200


def freeze():
    require(os.name == "nt", "protected sources stay on the Windows guest")
    spec, packet = method("heldout")
    source = loads(pinned(packet.parent / "Capture" / "Result.json", PROTECTED_SOURCE))
    require(spec["cohort"] == source["cohort"] == "heldout" and source["passed"]
            and source["job_sha256"] == METHODS["heldout"][1]
            and source["control_before"]["passed"] and source["control_after"]["passed"],
            "heldout construction requires the independently authored pre-writer source lock")
    from CompilePairCandidate import authored

    destination = PureWindowsPath(METHODS["heldout"][2])
    target = Path(destination.parent)
    require(not target.exists(), "protected candidate packet already exists")
    compiled = []
    for case, source_row in zip(spec["cases"], source["cases"], strict=True):
        (side,) = source_row["orientation"]
        require(source_row["case"] == case["name"] and source_row["passed"] and side in (0, 1),
                "protected hand is not an actual independently verified neutral selection")
        name = case["name"] + ".SLDPRT"
        neutral = authored(case, side)
        intent = dumps({"document": neutral.to_dict(), "epoch": EPOCH, "locator": str(destination / name)},
                       sort_keys=True, allow_nan=False).encode()
        packets = []
        for _ in range(2):
            run = subprocess.run((sys.executable, "-I", "-B", str(HERE/"CompilePairCandidate.py")), input=intent,
                                 capture_output=True, check=False, timeout=120)
            require(run.returncode == 0 and not run.stderr,
                    "protected neutral construction failed in an independent worker")
            packets.append(run.stdout)
        require(packets[0] == packets[1], "protected writer processes disagree")
        row = loads(packets[0])
        raw = b64decode(row.pop("archive"), validate=True)
        require(row["archive_sha256"] == digest(raw) and row["runtime_external_reads"] == 0,
                "protected candidate bytes or guard differ")
        compiled.append((row | {"name": name, "neutral_sha256": digest(intent), "guarded_processes": 2}, raw, intent))
    target.mkdir(parents=True, exist_ok=False)
    (target/"Candidates").mkdir()
    for index, (row, raw, intent) in enumerate(compiled):
        write_new(target/"Candidates"/row["name"], raw)
        write_new(target/("Neutral" + str(index) + ".json"), intent)
    for filename in ("RunPairCandidates.py", "CompareLockedPair.py"):
        write_new(target/filename, (HERE/filename).read_bytes())
    manifest = {"schema":"kit.sw2026.distance-pair-neutral-build.v1", "cohort":"heldout",
                "destination": str(destination), "written_at": EPOCH, "private_source_sha256": PROTECTED_SOURCE,
                "writer_revision": SOURCE_REVISION, "candidates":[row for row, _, _ in compiled]}
    raw = (dumps(manifest,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    write_new(target/"Generated.json", raw)
    return {"generation_sha256": digest(raw), "candidate_count": len(compiled), "guarded_workers": 4,
            "writer_revision": SOURCE_REVISION}


if __name__ == "__main__":
    print(dumps(freeze(), sort_keys=True))
