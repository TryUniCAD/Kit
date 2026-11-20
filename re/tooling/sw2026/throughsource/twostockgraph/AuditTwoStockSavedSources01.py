from hashlib import sha256
from math import isclose
from pathlib import Path
from subprocess import check_output, run
import base64
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
DATA = ROOT / "re/solidworks/measurements/2026"
SOURCE = ROOT / "re/solidworks/v2026/heldout/TwoStockWriterSourceLock01.json"
EVALUATION = DATA / "TwoStockWriterHoldoutNative02.json"
SOURCE_SHA = "1c07e988d425da1de7fd53ccdb30f7b18dc6b431236674404bcc1d8f3b21ae2c"
EVALUATION_SHA = "6b39921b4959e3662f886def026c55240227f8aab37d3246206bcf02ab8cbb7a"
SDK_TREE = "93f0ef018a2e403a5cf98ba2d832a2db16b362fa"
PYTHON = r"C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe"
GUEST_READ = """
from pathlib import Path
from hashlib import sha256
import base64
import json
import sys

root = Path("C:/KitSdkCandidates")
slot, role, record_pin = sys.argv[1:]
if slot not in ("a", "b") or role not in ("source", "derived"):
    raise ValueError("unrecognized completed evaluation arm")
if role == "source":
    folder = root / "TwoStockWriterHoldout01" / slot
    record = folder / "AutoReopen/Record.json"
    archive = folder / "AutoAuthor/ThroughMultiStock.SLDPRT"
    hash_key, phase = "opened_sha256", "before_edit"
else:
    folder = root / "TwoStockWriterEvaluation02" / slot
    record = folder / "Open/Record.json"
    archive = folder / "NativeAfterEdit.SLDPRT"
    hash_key, phase = "saved_sha256", "after_edit"
record_raw = record.read_bytes()
if record.is_symlink() or sha256(record_raw).hexdigest() != record_pin:
    raise ValueError("completed native record changed")
data = json.loads(record_raw)
result = data["result"]
raw = archive.read_bytes()
if archive.is_symlink() or not data["passed"] or sha256(raw).hexdigest() != result[hash_key]:
    raise ValueError("completed native save changed")
drivers = result[phase]["drivers"]
value = [drivers[name]["value_m"] * 1000 for name in ("SteadyStock", "MovingStock")]
print(json.dumps({"archive_b64": base64.b64encode(raw).decode(), "d1_mm": value}))
"""


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, expected):
    raw = path.read_bytes()
    if path.is_symlink() or digest(raw) != expected:
        raise ValueError("pinned held-out evidence changed")
    return json.loads(raw)


def guest(slot, role, record_pin):
    encoded = base64.b64encode(GUEST_READ.encode()).decode()
    program = f"import base64;exec(base64.b64decode('{encoded}'))"
    args = (
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        PYTHON,
        "-B",
        "-c",
        program,
        slot,
        role,
        record_pin,
    )
    last = None
    for _ in range(2):
        response = run(args, capture_output=True, timeout=90)
        if response.returncode == 0:
            return json.loads(response.stdout)
        last = response
        if response.returncode != 255 or b"PrlJob_" not in response.stderr:
            break
    diagnostic = last.stderr.decode(errors="replace").splitlines()[-2:]
    raise RuntimeError(
        f"{slot}/{role} record-only transport failed ({last.returncode}): {diagnostic}"
    )


def run_worker(raw):
    worker = HERE.with_name("ProveSavedStockReadback01.py")
    result = run(
        (sys.executable, "-I", "-B", str(worker), "--worker", "strict"),
        input=raw,
        capture_output=True,
        timeout=90,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode())
    return json.loads(result.stdout)


def prove():
    tree = check_output(("git", "rev-parse", "HEAD:src"), cwd=ROOT, text=True).strip()
    exact = run(("git", "diff", "--quiet", "HEAD", "--", "src"), cwd=ROOT).returncode
    if tree != SDK_TREE or exact:
        raise ValueError("the frozen SDK reader source tree changed")
    native = pinned(EVALUATION, EVALUATION_SHA)["native"]
    sources = pinned(SOURCE, SOURCE_SHA)["sources"]
    phases = {}
    for source in sources:
        slot = source["slot"]
        opened = native["cases"][slot]["native_phases"]["Open"]
        for role, record_pin in (
            ("source", source["phase_sha256"][1]),
            ("derived", opened["sha256"]),
        ):
            record = guest(slot, role, record_pin)
            raw = base64.b64decode(record["archive_b64"], validate=True)
            if role == "source" and digest(raw) != source["sha256"]:
                raise ValueError("original held-out source checksum changed")
            sdk = run_worker(raw)
            if sdk["sha256"] != digest(raw) or sdk["runtime_data_file_reads"] != 0:
                raise ValueError("SDK input or access evidence differs")
            if not all(
                isclose(a, b, rel_tol=5e-7, abs_tol=1e-10)
                for a, b in zip(sdk["d1_mm"], record["d1_mm"], strict=True)
            ):
                raise ValueError("strict SDK driving depths differ from native values")
            phases[slot + "/" + role] = {"native_record_sha256": record_pin, **sdk}
    return {
        "sdk_source_tree": tree,
        "tool_sha256": digest(HERE.read_bytes()),
        "heldout_native_receipt_sha256": EVALUATION_SHA,
        "source_lock_sha256": SOURCE_SHA,
        "guarded_read_processes": len(phases),
        "runtime_data_file_reads": 0,
        "new_native_processes": 0,
        "phases": phases,
    }


if __name__ == "__main__":
    print(json.dumps(prove(), sort_keys=True, indent=2, allow_nan=False))
