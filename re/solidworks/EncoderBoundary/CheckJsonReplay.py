from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
import zlib


CASES = (
    "BaselineReconstruction", "BaselineEdited",
    "HeldOutReconstruction", "HeldOutEdited",
)


def setup(root):
    sys.path[:0] = [str(root / "src"), str(root / "re"), str(root / "re/automation")]


def replay(root, request):
    setup(root)
    import EncoderRoundTrip.Solidworks as adapter
    from interchange.document.Models.DocumentModel import CadDocument

    prepared = CadDocument.from_json(request["prepared_json"])
    if prepared.brep is not None or prepared.brep_payloads or prepared.source.attributes or set(prepared.metadata) != {"name"}:
        raise ValueError("replay input retained native archive or wrapper state")
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    driver, = prepared.parameters
    inconsistent = replace(prepared, parameters=(replace(driver, value=replace(driver.value, value=driver.value.value + 1)),))
    extra = replace(prepared, metadata={**prepared.metadata, "unmodeled": True})
    admission = {
        adapter.prepare_generation_input.__code__, adapter.reconstruct.__code__,
        adapter._project_cold_source.__code__,
    }
    active = False
    denied = []
    source_calls = []

    def profile(frame, event, _):
        if active and event == "call" and frame.f_code in admission:
            source_calls.append(frame.f_code.co_name)
            raise RuntimeError("prepared generation attempted runtime source admission")

    def audit(event, _):
        if active and (
            event in (
                "open", "os.listdir", "os.scandir", "os.system", "os.exec",
                "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.forkpty",
            )
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            denied.append(event)
            raise PermissionError("prepared generation attempted external access: " + event)

    sys.addaudithook(audit)
    sys.setprofile(profile)
    active = True
    try:
        payload = adapter.generate_prepared_candidate(
            prepared, native_locator=request["native_locator"], written_at=request["written_at"],
        )
        actual = sha256(payload).hexdigest()
        if actual != request["expected_sha256"]:
            raise ValueError("fresh JSON replay differs from the independently generated candidate")
        refused = []
        for label, mutation in (("inconsistent_depth", inconsistent), ("extra_metadata", extra)):
            try:
                adapter.generate_prepared_candidate(
                    mutation, native_locator=request["native_locator"], written_at=request["written_at"],
                )
            except ValueError:
                refused.append(label)
            else:
                raise ValueError("prepared generation accepted unsupported state: " + label)
    finally:
        active = False
        sys.setprofile(None)
    if denied or source_calls or any(name.startswith(("win32com", "pythoncom")) for name in sys.modules):
        raise ValueError("prepared generation crossed the offline replay boundary")
    return {
        "role": request["role"], "sha256": actual, "bytes": len(payload),
        "measured_sha256": request["measured_sha256"],
        "measured_match": actual == request["measured_sha256"],
        "external_access_attempts": len(denied), "source_admission_calls": len(source_calls),
        "refusals": refused,
    }


def check(root):
    setup(root)
    from convert import open_document
    from EncoderRoundTrip.Solidworks import prepare_generation_input, generate_prepared_candidate
    from interchange.document.Models.DocumentModel import CadDocument
    from tooling.sw2026.PreparePlainPartEvidence import construct

    inputs = root / "re/solidworks/measurements/2026/EncoderRoundTrip"
    results = []
    exact_runtime = (
        sys.platform == "win32" and platform.machine() == "AMD64"
        and platform.python_version() == "3.14.6"
        and zlib.ZLIB_VERSION == zlib.ZLIB_RUNTIME_VERSION == "1.3.1.zlib-ng"
    )
    for role in CASES:
        source_role = role.replace("Edited", "Reconstruction")
        original = CadDocument.from_json((inputs / "Requests" / (source_role + ".json")).read_text(encoding="utf-8"))
        target = CadDocument.from_json((inputs / "Requests" / (role + ".json")).read_text(encoding="utf-8"))
        envelope = json.loads((inputs / (role + ".json")).read_bytes())
        epoch = envelope["written_at"]
        source_locator = rf"C:\KitEncoderRoundTrip\{original.metadata['name']}.SLDPRT"
        locator = rf"C:\KitEncoderRoundTrip\{target.metadata['name']}.SLDPRT"
        original_bytes = construct(original, source_locator, epoch).BytesValue
        cold = open_document(original_bytes, source_format="solidworks.sldprt", strict=True)
        edit = {"dimension": "depth", "value_mm": target.parameters[0].value.value} if role.endswith("Edited") else None
        prepared = prepare_generation_input(cold, edit, native_locator=locator, written_at=epoch)
        prepared_json = prepared.to_json()
        if prepared.brep is not None or prepared.brep_payloads or prepared.source.attributes or set(prepared.metadata) != {"name"}:
            raise ValueError("admitted constructor input retained native archive or wrapper state")
        expected = sha256(generate_prepared_candidate(prepared, native_locator=locator, written_at=epoch)).hexdigest()
        measured = envelope["receipt"]["builds"][0]["candidate_sha256"]
        if exact_runtime and expected != measured:
            raise ValueError("recorded runtime failed to regenerate the exact measured candidate")
        request = {
            "role": role, "prepared_json": prepared_json, "native_locator": locator,
            "written_at": epoch, "expected_sha256": expected, "measured_sha256": measured,
        }
        del cold, original_bytes, original, target, prepared
        with TemporaryDirectory(prefix="KitJsonOnlyReplay-") as empty:
            execution = subprocess.run(
                [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--root", str(root), "--worker"],
                input=json.dumps(request), cwd=empty, capture_output=True, text=True,
                timeout=90, check=False,
            )
        if execution.returncode != 0:
            raise ValueError(execution.stdout + execution.stderr)
        result = json.loads(execution.stdout)
        if exact_runtime and not result["measured_match"]:
            raise ValueError("fresh child failed exact measured digest binding")
        results.append(result)
    files = (
        "re/automation/EncoderRoundTrip/Solidworks.py", "re/tooling/sw2026/PreparePlainPartEvidence.py",
        "src/convert/adapters/solidworks/Core/Preparation/PlanPartWrite.py",
    )
    return {
        "schema": "kit.sw2026.json-only-constructor-replay.v1", "passed": True,
        "fresh_processes": len(results), "native_launches": 0,
        "native_source_files_written": 0, "exact_measured_runtime": exact_runtime,
        "runtime": {"python": platform.python_version(), "platform": sys.platform, "machine": platform.machine(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
        "method_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": {name: sha256((root / name).read_bytes()).hexdigest() for name in files},
        "results": results,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Replay prepared SOLIDWORKS constructor JSON in fresh guarded processes")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = replay(args.root.resolve(), json.load(sys.stdin)) if args.worker else check(args.root.resolve())
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
