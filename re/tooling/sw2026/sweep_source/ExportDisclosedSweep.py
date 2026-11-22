from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile


ROOT = Path(r"C:\KitSweepBossSource07")
EXPORT = Path(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SweepBossSource07\DisclosedNative")
LOCK_PIN = "563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca"
JOB_PIN = "e7a321d410d278b255fe4fe220d6ef5e2e35628b416646cc454bc5cf9b14f421"


def copy_checked(source, target, expected):
    if sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError("disclosed native artifact digest differs")
    copyfile(source, target)
    if sha256(target.read_bytes()).hexdigest() != expected:
        raise ValueError("disclosed transfer changed bytes")


def main():
    capture = ROOT / "Capture"
    spec = json.loads((ROOT / "Packet" / "Spec.json").read_bytes())
    lock = capture / "SourceLock.json"
    raw = lock.read_bytes()
    record = json.loads(raw)
    if not (sha256(raw).hexdigest() == LOCK_PIN and record["job_sha256"] == JOB_PIN
            and record["cohort"] == spec["cohort"] == "disclosed" and record["passed"]
            and record["distinct_processes"] == 12 and record["idle_after"]):
        raise ValueError("disclosed sweep lifecycle is outside the verified export scope")
    EXPORT.mkdir(exist_ok=False)
    for row in record["sources"]:
        slot = row["slot"]
        directory = capture / f"Slot{slot + 1:02d}"
        name = spec["cases"][slot]["name"]
        for role, expected in row["artifact_sha256"].items():
            label = name if role == "original" else name + role.title() + "Edit"
            file = f"{label}.SLDPRT"
            copy_checked(directory / file, EXPORT / file, expected)
        for phase in row["phases"]:
            copy_checked(directory / phase["phase"] / "Record.json",
                         EXPORT / f"Slot{slot + 1:02d}-{phase['phase']}.json",
                         phase["receipt_sha256"])
    copy_checked(lock, EXPORT / lock.name, LOCK_PIN)
    copy_checked(capture / "RegisteredApi.json", EXPORT / "RegisteredApi.json", record["api_sha256"])
    print(json.dumps({"disclosed_sources": 2, "verified_parts": 6, "source_lock_sha256": LOCK_PIN,
                      "native_processes_started": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
