from argparse import ArgumentParser
from io import BytesIO
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ProveColdCircleRepublish import (
    FORMAT, MEASURE, ROOT, CadDocument, FromData, OutputGuard, adapter,
    assert_result, digest, open_document, preload, registry, writer,
)

ORIGINALS = ("H01TranslatedDiameter", "H02ReverseTopCircle")
END_MODES = ("H03MidPlane", "H04TwoDirections")


def checked(path, sha256):
    data = path.read_bytes()
    if digest(data) != sha256:
        raise ValueError(f"unexpected historical digest for {path.name}")
    return data


def frozen_inputs(case, disclosure):
    paired = case in END_MODES
    if paired:
        custody = disclosure / "SdkPairedEndConditions02"
        freeze_sha = "0d9655b482e7aa46f80ddc2a000fd597f6a869a55c481aa227e9b9b9c9b0e987"
        request_path = custody / "Generated" / case / "Request.json"
        report_name = "SdkPairedEndConditionsNative01.json"
        report_sha = "08a866d4922298c892b2126f71adca26ac9ae3f96421f6a0ed9ab77195607ca4"
    else:
        custody = disclosure / "SdkCircleOriginalHeldouts01"
        freeze_sha = "106a33bdcbb1d03fb332cd13e90bc90d48dc5c01691b200a956bc3e92660c652"
        request_path = custody / case / "Request.json"
        report_name = "SdkOriginalCircleNative01.json"
        report_sha = "a14c4ff431f4e75b129025072d8be8f752df2694467b8c743b0ce861b0401da5"
    freeze = loads(checked(custody / "GeneratedFreeze.json", freeze_sha))
    (frozen,) = (row for row in freeze["cases"] if row["name"] == case)
    request_sha = frozen["request_sha256"]
    request = loads(checked(request_path, request_sha))
    report_text = checked(ROOT / "re/solidworks/measurements/2026" / report_name, report_sha).decode("utf-8")
    report = loads(report_text)
    (observed,) = (row for row in report["cases"] if row["name"] == case)
    expected = frozen["candidate_sha256"]
    if paired:
        assert report["native_acceptance"] and report["generated"][case] == expected
        assert report["generated_freeze_sha256"] == freeze_sha
    else:
        assert report["scoped_sdk_heldout_acceptance"]
        assert observed["lanes"]["generated"]["input_sha256"] == expected
    return request, request_sha, report_text, report_sha, expected


def replay(case, disclosure, scratch):
    request, request_sha, report_text, report_sha, expected = frozen_inputs(case, disclosure)
    leaf = case + ".SLDPRT"
    values = {
        "final_destination": str(PureWindowsPath(r"C:\KitSdkCandidates", leaf)),
        MEASURE: {"written_at": request["created_at"], "receipt": {"native_report": report_text}},
        "allow_carrier": False,
        "require_native_transfers": True,
    }
    source = FromData(request["document"])
    source.assert_valid()
    preload()
    guard = OutputGuard(scratch, leaf)
    sys.addaudithook(guard.audit)
    routes = {}
    with guard.active("memory"):
        for route in (registry, writer, adapter):
            sink = BytesIO()
            result = route(source, sink, values)
            payload = sink.getvalue()
            assert digest(payload) == expected
            assert_result(result, source, payload)
            readbacks = {}
            for full in (True, False):
                read = open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=full)
                restored = CadDocument.from_json(read.to_json(indent=None))
                assert restored == read and (read.brep is not None) is full
                sink = BytesIO()
                result = route(restored, sink, values)
                assert_result(result, read, payload)
                assert sink.getvalue() == payload
                readbacks["full" if full else "design_only"] = digest(sink.getvalue())
            routes[route.__name__] = {"authored": digest(payload), "readback": readbacks}
    assert not guard.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
    return {
        "case": case, "frozen_request_sha256": request_sha, "report_sha256": report_sha,
        "native_tested_sha256": expected, "routes": routes, "runtime_reads": len(guard.denied),
        "frozen_source_cad_files_opened": 0, "native_processes_launched": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--case", required=True, choices=(*ORIGINALS, *END_MODES))
    parser.add_argument("--disclosure", required=True, type=Path)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitOriginalCircle-") as work:
        result = replay(args.case, args.disclosure.resolve(), Path(work).resolve())
    print(dumps(result, indent=2, sort_keys=True, allow_nan=False))
