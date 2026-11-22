from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import (
    KMeasureRoot,
    MeasurePlainDoc,
)


# a fresh guarded process exercises the installed writer with authentic disclosed in memory evidence
def RunPlainCase(RoleName: str) -> dict[str, object]:
    DocumentValue, Envelope, Digest = MeasurePlainDoc(RoleName)
    NameValue = CastValue(str, DocumentValue.metadata["name"])
    Command = KMeasureRoot / "re/tooling/sw2026/CheckMeasuredPartWriter.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Command), "--root", str(KMeasureRoot), "--worker"),
        input=DumpJson(
            {
                "document": LoadJson(DocumentValue.to_json()),
                "evidence": Envelope,
                "expected_locator": rf"C:\KitSdkCandidates\{NameValue}.SLDPRT",
                "role": RoleName,
                "sha256": Digest,
            }
        ),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_input_file_reads"] == 0
    assert ReportValue["sha256"] == Digest
    return ReportValue
