from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import sys


def check(root):
    sys.path[:0] = [str(root / "src"), str(root)]
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc

    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    cases = [(role, *MeasurePlainDoc(role)) for role in ("Skew", "Step")]
    blocked = []
    active = False

    def audit(event, arguments):
        if active and (
            event in (
                "open", "os.listdir", "os.scandir", "os.system", "os.exec",
                "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.forkpty",
            )
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            blocked.append(event)
            raise PermissionError("public writer attempted external access: " + event)

    sys.addaudithook(audit)
    results = []
    for role, document, envelope, expected in cases:
        locator = rf"C:\KitSdkCandidates\{document.metadata['name']}.SLDPRT"
        options = {"final_destination": locator, "solidworks_native_measurement": envelope}
        active = True
        try:
            candidate = PrepareNative(document, BytesIO(), envelope["written_at"], WriteOptions(values={"final_destination": locator}))
            streams = BytesIO(), BytesIO()
            outcomes = (
                write_document(document, streams[0], destination_format="solidworks.sldprt", allow_carrier=False, values=options),
                SldprtWriter().write(document, streams[1], WriteOptions(values=options)),
            )
            if any(sha256(stream.getvalue()).hexdigest() != expected for stream in streams):
                raise ValueError("public streams differ from exact historical measurement")
            if streams[0].getvalue() != streams[1].getvalue() or streams[0].getvalue() != candidate.BytesValue:
                raise ValueError("public streams differ from regenerated candidate")
            if not all(result.vendor_loadable and result.application_usable and not result.dropped for result in outcomes):
                raise ValueError("public result does not retain measured acceptance")
            feature, = document.feature_timeline
            parameter, = document.parameters
            length = replace(parameter.value, value=parameter.value.value + 1)
            changed = replace(document, parameters=(replace(parameter, value=length),), feature_timeline=(replace(feature, definition=replace(feature.definition, length=length)),))
            bad_build, missing_reopen, failed_control = (deepcopy(envelope) for _ in range(3))
            bad_build["receipt"]["oracle"]["build"] = "34.4.1.1011"
            next(phase for phase in missing_reopen["receipt"]["phases"] if phase["role"] == role + "Reopen")["role"] = "MissingReopen"
            failed_control["receipt"]["phases"][0]["passed"] = False
            requests = (
                ("missing_receipt", document, None, locator, "offline native measurement receipt"),
                ("changed_model", changed, envelope, locator, "no unique exact native measurement"),
                ("different_epoch", document, envelope | {"written_at": envelope["written_at"] + 1}, locator, "no unique exact native measurement"),
                ("different_locator", document, envelope, "C:\\UnmeasuredOutput\\" + locator.rsplit("\\", 1)[-1], "no unique exact native measurement"),
                ("bad_build", document, bad_build, locator, "exact passing SOLIDWORKS"),
                ("missing_reopen", document, missing_reopen, locator, "matched candidate lifecycle"),
                ("failed_control", document, failed_control, locator, "failed an oracle phase"),
            )
            refusals = []
            for label, model, evidence, path, message in requests:
                values = {"final_destination": path}
                if evidence is not None:
                    values["solidworks_native_measurement"] = evidence
                for mode in ("registry", "direct"):
                    stream = BytesIO(b"preserve stream")
                    stream.seek(3)
                    try:
                        if mode == "registry":
                            write_document(model, stream, destination_format="solidworks.sldprt", values=values)
                        else:
                            SldprtWriter().write(model, stream, WriteOptions(values=values))
                    except ValueError as error:
                        if message not in str(error):
                            raise ValueError(f"wrong {label} refusal: {error}") from error
                    else:
                        raise ValueError("unmeasured request crossed publication: " + label)
                    if stream.getvalue() != b"preserve stream" or stream.tell() != 3:
                        raise ValueError("refused publication changed caller stream")
                refusals.append(label)
            results.append({"role": role, "sha256": expected, "bytes": len(candidate.BytesValue), "accepted_streams": 2, "refusals": refusals})
        finally:
            active = False
    if blocked or any(name.startswith(("pythoncom", "win32com")) for name in sys.modules):
        raise ValueError("public writing crossed the offline boundary")
    source = root / "src/convert/adapters/solidworks/Core"
    files = (
        "Preparation/PrepareNative.py", "Writing/EmitNativeMut.py",
        "Writing/Measured/ReadPartMeas.py", "Writing/Measured/MatchPartMeas.py",
        "Writing/Measured/MatchMeasCase.py", "Writing/Measured/MeasPhaseMap.py",
        "Writing/Measured/CheckMeasSlot.py",
    )
    return {
        "schema": "kit.sw2026.encoder-publication-boundary.v1",
        "passed": True, "native_launches": 0,
        "runtime_external_accesses": len(blocked),
        "evidence_scope": "historical_receipt_replay_only", "results": results,
        "method_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": {"src/convert/adapters/solidworks/Core/" + name: sha256((source / name).read_bytes()).hexdigest() for name in files},
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Check exact historical SOLIDWORKS public stream receipt bindings without CAD")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check(args.root.resolve())
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
