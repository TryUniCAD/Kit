from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from zlib import ZLIB_RUNTIME_VERSION


CASES = (
    "BaselineReconstruction", "BaselineEdited",
    "HeldOutReconstruction", "HeldOutEdited",
)


def refuse(write, document, options, expected_error):
    protected = BytesIO(b"caller-owned output")
    protected.seek(4)
    try:
        write(document, protected, options)
    except ValueError as error:
        if expected_error not in str(error):
            raise
    else:
        raise ValueError(f"unqualified publication passed: {expected_error}")
    if protected.getvalue() != b"caller-owned output" or protected.tell() != 4:
        raise ValueError("refusal changed caller-owned output")


def check(root):
    sys.path[:0] = [str(root / "src"), str(root / "re")]
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument
    from tooling.sw2026.PreparePlainPartEvidence import construct

    active = False
    blocked = []
    guarded_calls = 0

    def audit(event, _):
        if active and (
            event in (
                "open", "os.listdir", "os.scandir", "os.system", "os.exec",
                "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.forkpty",
            )
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            blocked.append(event)
            raise PermissionError("cold public writer attempted external access: " + event)

    sys.addaudithook(audit)

    def registry(document, stream, options):
        nonlocal active, guarded_calls
        active = True
        guarded_calls += 1
        try:
            return write_document(
                document, stream, destination_format="solidworks.sldprt",
                allow_carrier=False, values=options,
            )
        finally:
            active = False

    def direct(document, stream, options):
        nonlocal active, guarded_calls
        active = True
        guarded_calls += 1
        try:
            return SldprtWriter().write(document, stream, WriteOptions(values=options))
        finally:
            active = False

    inputs = root / "re/solidworks/measurements/2026/EncoderRoundTrip"
    results = []
    for role in CASES:
        request = CadDocument.from_json((inputs / "Requests" / f"{role}.json").read_text(encoding="utf-8"))
        envelope = json.loads((inputs / f"{role}.json").read_bytes())
        receipt = envelope["receipt"]
        locator = rf"C:\KitEncoderRoundTrip\{request.metadata['name']}.SLDPRT"
        candidate = construct(request, locator, envelope["written_at"]).BytesValue
        expected = receipt["builds"][0]["candidate_sha256"]
        replay_sha = sha256(candidate).hexdigest()
        document = open_document(candidate, source_format="solidworks.sldprt", strict=True)
        document = CadDocument.from_json(document.to_json())
        options = {"final_destination": locator, "solidworks_native_measurement": envelope}
        edited_identity = deepcopy(envelope)
        edited_identity["receipt"]["oracle"]["sha256"] = "0" * 64
        edited_volume = deepcopy(envelope)
        edited_center = deepcopy(envelope)
        initial_volume = next(phase for phase in edited_volume["receipt"]["phases"] if phase["role"] == role + "Generated")["states"][0]
        initial_center = next(phase for phase in edited_center["receipt"]["phases"] if phase["role"] == role + "Generated")["states"][0]
        initial_volume["volume_m3"] = 10**400
        initial_center["centre_of_mass_m"][0] = -(10**400)
        accepted = 0
        oversized_refused = 0
        for write in (registry, direct):
            refuse(
                write, document, {**options, "solidworks_native_measurement": edited_identity},
                "exact passing SOLIDWORKS",
            )
            if replay_sha != expected:
                if sys.platform == "win32" and "zlib-ng" in ZLIB_RUNTIME_VERSION:
                    raise ValueError(f"measured compression runtime failed to reproduce {role}")
                refuse(write, document, options, "no unique exact native measurement")
                continue
            for malformed in (edited_volume, edited_center):
                refuse(
                    write, document, {**options, "solidworks_native_measurement": malformed},
                    "finite scalar observations",
                )
                oversized_refused += 1
            stream = BytesIO()
            result = write(document, stream, options)
            measured = result.metadata["solidworks_native_measurement"]
            if (
                stream.getvalue() != candidate or result.dropped
                or not result.vendor_loadable or not result.application_usable
                or measured["oracle_build"] != receipt["oracle"]["build"]
            ):
                raise ValueError(f"publication lost archive or oracle binding: {role}")
            accepted += 1
        results.append({
            "role": role, "accepted": accepted, "unknown_identity_refused": 2,
            "oversized_measurement_refused": oversized_refused,
        })
    if blocked or any(name.startswith(("pythoncom", "win32com")) for name in sys.modules):
        raise ValueError("cold public writing crossed the offline boundary")
    source = root / "src/convert/adapters/solidworks/Core"
    files = (
        "Preparation/PrepareNative.py", "Preparation/Readback/CheckColdRead.py",
        "Writing/EmitNativeMut.py", "Writing/Measured/ReadPartMeas.py",
        "Writing/Measured/MeasState.py", "Writing/Measured/ReadMeasNum.py",
    )
    return {
        "results": results, "zlib_runtime": ZLIB_RUNTIME_VERSION,
        "evidence_scope": "strict_cold_json_public_sdk", "guarded_public_calls": guarded_calls,
        "runtime_external_accesses": len(blocked), "native_launches": 0,
        "method_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": {"src/convert/adapters/solidworks/Core/" + name: sha256((source / name).read_bytes()).hexdigest() for name in files},
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.root.resolve()), sort_keys=True))
