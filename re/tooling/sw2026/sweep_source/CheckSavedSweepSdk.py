from argparse import ArgumentParser
from base64 import b64decode
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src")]

from AuditSavedSweepMain import LOCK, ORACLE, checked, demand, disclosed, git
from AuditSavedSweepTopology import native_measurement

TOPOLOGY = "e1cb4806e4de56f3d03875a5a6a804956f00b7f00e7e48ba34cf7a523696aff2"
SOURCE_BASE = "b05889d997f67a8f862265ee236678610dfe4eef"
RECEIPT_PATH = ROOT / "re/solidworks/measurements/2026/ScopedSavedSweepTopology01.json"


def job_bytes(job):
    raw = b64decode(job["payload"], validate=True)
    demand(sha256(raw).hexdigest() == job["file_sha256"], "disclosed payload differs from its locked SHA")
    return raw


def preload():
    for codec in ("utf-8-sig", "utf-8", "utf-16-le", "ascii", "latin-1", "cp1252"):
        lookup(codec)
    for module in (
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)


def worker(job):
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Container.Format import KPartFormatId
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Writing.CanWriteSweep import CanWriteSweep
    from interchange.document.Models.DocumentModel import CadDocument
    from SavedSweepReplay import guard_runtime
    from SavedSweepSdkModel import compare_model, manager_stamp, negative_contrasts

    raw = job_bytes(job)
    foreign = job_bytes(job["foreign"])
    preload()
    attempts = guard_runtime()
    adapter = SldprtAdapter()
    direct = adapter.read(raw, ReadOptions())
    registry = open_document(BytesIO(raw), source_format=KPartFormatId)
    document = adapter.read(raw, ReadOptions(configuration="Default"))
    reduced = open_document(BytesIO(raw), source_format=KPartFormatId, configuration="Default", include_brep=False)
    receipt = compare_model(direct, (registry, document), reduced, job)
    receipt["joined_manager_stamp"] = manager_stamp(raw)
    text = direct.to_json(indent=None)
    decoded = CadDocument.from_json(text)
    demand(decoded == direct and decoded.to_json(indent=None) == text, "portable JSON changed a saved sweep owner")
    demand(not CanWriteSweep(direct, BytesIO()) and not CanWriteSweep(reduced, BytesIO()),
           "native saved source unexpectedly entered the cold output authorization route")
    contrasts = negative_contrasts(raw, foreign, job["slot"], job["role"])
    demand(not attempts and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "strict saved reader used runtime files or CAD")
    return {"slot": job["slot"], "role": job["role"], "source_sha256": job["file_sha256"],
            "native_phase_sha256": job["native_phase"]["sha256"], "source_observation": receipt,
            "neutral_json_sha256": sha256(text.encode("utf-8")).hexdigest(), "runtime_accesses": len(attempts),
            "cold_writers_refused": 2, "owner_contrast_refusals": contrasts}


def source_manifest():
    changed = git("diff", "--name-only", SOURCE_BASE, "--", "src").decode().splitlines()
    new = git("ls-files", "--others", "--exclude-standard", "--", "src").decode().splitlines()
    paths = sorted(set(changed + new))
    manifest = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    return {"base": SOURCE_BASE, "files": len(manifest),
            "sha256": sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def supervise(directory):
    lock, jobs = disclosed(directory)
    measured = json.loads(checked(RECEIPT_PATH, TOPOLOGY))
    rows = {(row["slot"], row["role"]): row for row in measured["states"]}
    results = []
    for job in jobs:
        slot, role = job["slot"], job["role"]
        recorded = rows[slot, role]
        demand(recorded["file_sha256"] == job["file_sha256"], "prior verified topology came from another save")
        comparison = rows[slot, "original"]
        job["prior"] = {"saved_sketches": recorded["saved_sketches"], "topology": recorded["topology"],
                        "geometry": recorded["geometry"], "original_radii_m": comparison["geometry"]["radii_m"]}
        job["native_measurement"] = native_measurement(directory, job)
        alternate = next(source for source in jobs if source["slot"] != slot and source["role"] == role)
        job["foreign"] = {name: alternate[name] for name in ("payload", "file_sha256")}
        proc = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(job),
                   capture_output=True, encoding="utf-8", check=False, timeout=45)
        demand(proc.returncode == 0 and not proc.stderr, proc.stderr or proc.stdout)
        results.append(json.loads(proc.stdout))
    paths = [HERE, HERE.with_name("SavedSweepSdkModel.py"), HERE.with_name("SavedSweepSdkTrims.py")]
    return {"schema": "kit.sw2026.saved-sweep-strict-reader.v1", "source_lock_sha256": LOCK,
            "topology_receipt_sha256": TOPOLOGY, "oracle_file_version": lock["oracle_build"], "oracle_sha256": ORACLE,
            "control_receipt_sha256": {name: item["receipt_sha256"] for name, item in lock["controls"].items()},
            "method_sha256": {file.name: sha256(file.read_bytes()).hexdigest() for file in paths},
            "fresh_sdk_processes": len(results), "source_manifest": source_manifest(),
            "python": sys.version.split()[0], "native_calls": 0, "published_archives": 0,
            "writer_admission_credits": 0, "heldout_credits": 0, "results": results}


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure strict SDK readback for exactly the six disclosed saved sweep files")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--disclosed", type=Path)
    args = parser.parse_args()
    value = worker(json.load(sys.stdin)) if args.worker else supervise(args.disclosed)
    print(json.dumps(value, sort_keys=True, indent=2, allow_nan=False))
