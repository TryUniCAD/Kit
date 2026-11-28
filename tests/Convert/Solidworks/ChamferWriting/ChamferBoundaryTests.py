from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue
from zlib import ZLIB_RUNTIME_VERSION as DeflateRuntime


# fresh workers exercise shipping public adapters without relying on in process setup
def RunChmfProof(WorkerName: str, *Arguments: str) -> dict[str, object]:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026" / WorkerName
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Worker), *Arguments),
        cwd=RootValue,
        capture_output=True,
        encoding="utf-8",
        timeout=110,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))


# both verified source modes retain all native rows in sdk and normal cli json
def TestChamferJson() -> None:
    for SlotValue in ("0", "1"):
        Report = RunChmfProof("CheckChmfJsonBoundary.py", "--slot", SlotValue)
        assert Report["ordered_rows"] == 20
        assert Report["native_rows"] == Report["cli_native_rows"] == 18
        assert Report["json_routes"] == Report["cli_publications"] == 2
        assert Report["sdk_refusals"] == 16 and Report["cli_refusals"] == 2
        assert Report["runtime_input_reads"] == Report["cad_launches"] == 0
        CountValue = Report["native_republication_routes"]
        assert CountValue == 2 or (CountValue == 0 and "zlib-ng" in DeflateRuntime)


# alternate container bytes must preserve the authenticated json source without authorizing native publication
def TestJsonDeflate() -> None:
    for SlotValue in ("0", "1"):
        Report = RunChmfProof("CheckChmfDeflate.py", "--slot", SlotValue)
        assert Report["original_sha256"] == Report["snapshot_source_sha256"]
        assert Report["alternate_sha256"] != Report["original_sha256"]
        assert Report["ordered_rows"] == 20 and Report["native_rows"] == 18
        assert Report["logical_streams"] == 10 and Report["json_routes"] == 2
        assert Report["measured_original"] is Report["cli_repeated_exact"] is True
        assert (
            Report["first_checks"]
            == Report["repeated_checks"]
            == {
                "compile": 1,
                "verify": 1,
            }
        )
        assert Report["sdk_refusals"] == 12 and Report["cli_refusals"] == 5
        assert Report["native_refusals"] == 2
        assert Report["runtime_reads"] == Report["native_processes"] == 0


# a separate synthetic keyword must not disable actual preexisting stock and cut projection
def TestMixedChmf() -> None:
    Report = RunChmfProof("CheckChmfMixedRead.py")
    assert Report["boundary_kind"] == "synthetic_keyword_only"
    assert Report["native_mixed_saves"] == 0
    assert Report["strict_refusals"] == Report["permissive_warnings"] == 2
    assert Report["typed_stock_ids"] == ["sldprt:feature:34", "sldprt:feature:46"]
    assert len(CastValue(list[str], Report["raw_payload_sha256"])) == 4
