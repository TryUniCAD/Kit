from base64 import b64decode, b64encode
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
MEASURE = (
    ROOT / "re/solidworks/measurements/2026/SdkLockedRevolveNativeComparison01.json"
)
RECEIPT_PIN = "b75858c3422bfcc9379a4262fd12fdeeaa20c44fb54a489d54b5a4a9f83f2a8c"
PACKET = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover/SdkLockedRevolve02")
GUEST = PureWindowsPath("C:/KitSdkCandidates/SdkLockedRevolve02")
PYTHON = r"C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe"
AGGREGATE_TREE = "f8f88d07e8c973fc7e2d0c61418ba4e6923b01ab"
GUEST_CODE = r"""from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from subprocess import run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
import sys
tool, pin, archive, source_pin, request = sys.argv[1:]
path = Path(tool)
data = path.read_bytes()
if sha256(data).hexdigest() != pin:
    raise ValueError("guest replay tool differs")
source = Path(archive).read_bytes()
if sha256(source).hexdigest() != source_pin:
    raise ValueError("guest replay source archive differs")
with TemporaryDirectory(prefix="KitRevolveReplay-") as temporary:
    code = Path(temporary) / "Code"
    code.mkdir()
    with open_tar(fileobj=BytesIO(source), mode="r:") as tar:
        tar.extractall(code, filter="data")
    result = run(
        (sys.executable, "-I", "-S", "-B", tool, "--worker", temporary),
        input=b64decode(request, validate=True), capture_output=True, timeout=60,
    )
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
raise SystemExit(result.returncode)
"""


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    if path.is_symlink() or digest(raw) != expected:
        raise ValueError("the previously measured packet changed")
    return raw


def guest_bytes(path, pin):
    code = (
        "from base64 import b64encode\nfrom pathlib import Path\nimport sys\n"
        "sys.stdout.buffer.write(b64encode(Path(sys.argv[1]).read_bytes()))"
    )
    args = (
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        PYTHON,
        "-B",
        "-c",
        code,
        str(path),
    )
    last = None
    for _ in range(2):
        last = run(args, capture_output=True, timeout=90)
        if last.returncode == 0:
            raw = b64decode(last.stdout, validate=True)
            if digest(raw) != pin:
                raise ValueError("the prior completed artifact differs")
            return raw
        if last.returncode != 255 or b"PrlJob_" not in last.stderr:
            break
    raise RuntimeError("previous completed record transport failed")


def compare_streams(before, after):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    prior = SldprtArchive.from_bytes(before).streams
    current = SldprtArchive.from_bytes(after).streams
    if set(prior) != set(current):
        raise ValueError("current logical stream inventory differs")
    changed = {}
    for name in sorted(prior):
        old, new = prior[name], current[name]
        if old == new:
            continue
        changed[str(name)] = {
            "previous_bytes": len(old),
            "current_bytes": len(new),
            "previous_sha256": digest(old),
            "current_sha256": digest(new),
            "first_difference": next(
                (index for index, pair in enumerate(zip(old, new)) if pair[0] != pair[1]),
                min(len(old), len(new)),
            ),
        }
    return {"stream_count": len(prior), "changed": changed}


def source_request(freeze, generation):
    from EvaluateLockedRevolve01 import encode

    case = generation["case"]
    if case["name"] != "RevolveHeldoutFirst" or freeze["slot"] != case["name"]:
        raise ValueError("only the previously consumed first case may be read")
    expected_locator = GUEST / "Candidate" / ("Kit" + case["name"] + ".SLDPRT")
    if PureWindowsPath(freeze["candidate"]) != expected_locator:
        raise ValueError("prior candidate locator differs")
    target = {
        "name": "Kit" + case["name"],
        "radial_mm": [value * 1000 for value in case["radius_m"]],
        "axial_mm": [value * 1000 for value in case["axial_m"]],
        "axis_x_mm": case["axis_x_m"] * 1000,
        "axis_span_mm": [value * 1000 for value in case["axis_axial_m"]],
        "angle_deg": case["angle_deg"],
        "reverse": case["reverse"],
        "edit_angle_deg": case["edit_angle_deg"],
        "created_at": freeze["epoch"],
        "self_path": str(expected_locator),
    }
    raw = encode({"neutral": target, "expected": generation["expected"]["initial"]})
    if digest(raw) != generation["neutral_request_sha256"]:
        raise ValueError("the previously used neutral request differs")
    return raw


def worker(root):
    sys.path.insert(0, str(HERE.parent.parent / "Preparation"))
    from EvaluateLockedRevolve01 import worker as prepare

    prepare(root, "build")


def build_candidate(launcher, request, count):
    runs = [launcher(request) for _ in range(count)]
    for started in runs:
        if started.returncode:
            raise RuntimeError(started.stderr.decode())
    if any(result.stdout != runs[0].stdout for result in runs[1:]):
        raise ValueError("guarded preparation is not deterministic")
    output = json.loads(runs[0].stdout)
    body = b64decode(output.pop("payload"), validate=True)
    if digest(body) != output["payload_sha256"] or output["runtime_external_attempts"] != 0:
        raise ValueError("emitted bytes or guard evidence differ")
    return output, body


def host_launcher(scratch):
    def launch(request):
        return run(
            (sys.executable, "-I", "-S", "-B", str(HERE), "--worker", str(scratch)),
            input=request,
            capture_output=True,
            timeout=90,
        )

    return launch


def guest_launcher(packet, archive_pin):
    share = PureWindowsPath(r"\\Mac\Home")
    guest_root = share.joinpath(*packet.relative_to(Path("/Users/odin")).parts)
    tool = guest_root.joinpath(*HERE.relative_to(ROOT).parts)

    def launch(request):
        command = (
            "prlctl", "exec", "Windows 11", "--current-user", PYTHON, "-I", "-S", "-B",
            "-c", "exec(bytes.fromhex('" + GUEST_CODE.encode().hex() + "'))",
            str(tool), digest(HERE.read_bytes()), str(guest_root / "Sdk.tar"),
            archive_pin, b64encode(request).decode("ascii"),
        )
        for _ in range(2):
            result = run(command, capture_output=True, timeout=90)
            if result.returncode != 255 or b"PrlJob_" not in result.stderr:
                break
        return result

    return launch


def guest_candidate(request, revision):
    sdk = check_output(("git", "archive", "--format=tar", revision, "src"), cwd=ROOT)
    with TemporaryDirectory(prefix="RevolveReplay-", dir=PACKET.parent) as name:
        packet = Path(name)
        (packet / "Sdk.tar").write_bytes(sdk)
        for path in (
            HERE,
            HERE.with_name("EvaluateLockedRevolve01.py"),
            HERE.parent.parent / "Preparation/MakeRevolveRequest01.py",
            HERE.parent.parent / "Preparation/ReadRevolveInput01.py",
        ):
            target = packet / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        return build_candidate(guest_launcher(packet, digest(sdk)), request, 1)


def prove():
    from EvaluateLockedRevolve01 import sdk_code

    head = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    tree = check_output(("git", "rev-parse", "HEAD:src"), cwd=ROOT, text=True).strip()
    if (
        tree != AGGREGATE_TREE
        or run(("git", "diff", "--quiet", "HEAD", "--", "src"), cwd=ROOT).returncode
    ):
        raise ValueError("the measured aggregate source tree differs")
    prior = json.loads(checked(MEASURE, RECEIPT_PIN))
    freeze = json.loads(checked(PACKET / "Freeze.json", prior["freeze_sha256"]))
    for name in ("MakeRevolveRequest01.py", "ReadRevolveInput01.py"):
        checked(
            HERE.parent.parent / "Preparation" / name, freeze["files"]["Tools/" + name]
        )
    checked(
        HERE.with_name("EvaluateLockedRevolve01.py"),
        freeze["files"]["Tools/EvaluateLockedRevolve01.py"],
    )
    evidence = json.loads(guest_bytes(GUEST / "Generation.json", prior["generation_sha256"]))
    if (
        evidence["freeze_sha256"] != prior["freeze_sha256"]
        or evidence["candidate_sha256"] != prior["generated_part_sha256"]
    ):
        raise ValueError("the past native candidate differs")
    request = source_request(freeze, evidence)
    with TemporaryDirectory(prefix="KitExistingRevolveReplay-") as name:
        scratch = Path(name)
        current_scratch = scratch / "Current"
        (current_scratch / "Code").mkdir(parents=True)
        (current_scratch / "Code/src").symlink_to(ROOT / "src")
        output, body = build_candidate(host_launcher(current_scratch), request, 2)
        prior_scratch = scratch / "Prior"
        prior_scratch.mkdir()
        sdk_code(PACKET, prior_scratch, freeze, extract=True)
        prior_host, prior_host_body = build_candidate(host_launcher(prior_scratch), request, 1)
    current_guest, current_guest_body = guest_candidate(request, head)
    previous = guest_bytes(PureWindowsPath(freeze["candidate"]), prior["generated_part_sha256"])
    return {
        "schema": "kit.sw2026.previously-consumed-revolve-replay.v1",
        "code_revision": head,
        "production_source_tree": tree,
        "old_native_receipt_sha256": RECEIPT_PIN,
        "neutral_request_sha256": digest(request),
        "prior_candidate_sha256": prior["generated_part_sha256"],
        "current": output,
        "candidate_bytes": len(body),
        "exact_previous_bytes": digest(body) == prior["generated_part_sha256"],
        "logical_comparison": compare_streams(previous, body),
        "old_writer_on_current_host": prior_host,
        "exact_old_writer_on_current_host": body == prior_host_body,
        "old_writer_host_comparison": compare_streams(previous, prior_host_body),
        "current_writer_on_oracle_host": current_guest,
        "exact_current_writer_on_oracle_host": current_guest_body == previous,
        "current_writer_oracle_host_comparison": compare_streams(previous, current_guest_body),
        "guarded_processes": 4,
        "new_native_runs": 0,
        "new_heldout_credit": 0,
        "original_source_reads": 0,
        "tool_sha256": digest(HERE.read_bytes()),
    }


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parent))
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]))
    else:
        print(json.dumps(prove(), sort_keys=True, indent=2, allow_nan=False))
