from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess
from subprocess import run as RunProcess
from sys import executable as PythonExec

# the disclosed native save is a read fixture with independently measured text
KFixture = (
    FilePath(__file__).resolve().parents[4]
    / "re/solidworks/v2026/corpus/part-properties/CircularProperties.SLDPRT"
)

# the authored ladder boss retains a solid and uses the unqualified advanced property manager
KRefusal = KFixture.parents[1] / "ladder/L1_boss.SLDPRT"

# the isolated wheel uses the older native example as its first conversion
KLegacyFixture = KFixture.parents[3] / "examples/.SLDPRT/example.SLDPRT"

# scope values come from the native author observation including the repeated custom name
KNativeText = [
    {
        "title": "Radial coupon β",
        "keywords": "ring & diameter",
        "comments": 'Gauge with "soft" jaws.',
    },
    {
        "KitMaterialNote": "Ring stock β",
        "KitBatch": "Run B7 & B8",
        "KitRevision": 'fit "R2" <limit>',
    },
    {
        "KitSetting": "Diameter option",
        "KitRevision": 'Configuration "Q4"',
    },
]


# the installed sdk is exercised in a fresh process for each disclosed native source
def StartTextRead(FixturePath: FilePath, *Options: str) -> CompletedProcess[str]:
    WorkerPath = FilePath(__file__).with_name("ReadLiteralPart.py")
    return RunProcess(
        (PythonExec, "-I", "-B", str(WorkerPath), str(FixturePath), *Options),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


# the queue checks all three native text scopes through the ordinary sdk process
def TestLiteralText() -> None:
    Outcome = StartTextRead(KFixture)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert (
        ReportValue["source_sha256"]
        == "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23"
    )
    assert ReportValue["status"]["status"] == "complete"
    assert ReportValue["status"]["configuration_ids"] == [0]
    assert ReportValue["text"] == KNativeText
    assert ReportValue["text_scopes"] == [True, True, True]
    assert ReportValue["configuration"] == ["modeled default", True, 0]
    assert ReportValue["body"] == ["sldprt:body:1", 1, 1, 1]


# strict open keeps the solid and strict conversion refuses to omit the unsupported text scopes
def TestTextRefusal() -> None:
    Outcome = StartTextRead(KRefusal, "--convert-refusal")
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert (
        ReportValue["source_sha256"]
        == "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
    )
    assert ReportValue["status"]["status"] == "unsupported"
    assert ReportValue["diagnostics"] == ["solidworks.part_text_properties_unavailable"]
    assert ReportValue["text"] == [None, None, None]
    assert ReportValue["text_scopes"] == [False, False, False]
    assert ReportValue["configuration"] == ["Default", True, 0]
    assert ReportValue["body"] == ["sldprt:body:1", 1, 1, 1]
    assert ReportValue["conversion"] == (
        "SOLIDWORKS part text properties are unavailable for strict cross-format conversion"
    )


# the strict path must preserve the legacy wheel route and refuse an actual authored legacy value
def TestLegacyText() -> None:
    Outcome = StartTextRead(KLegacyFixture, "--legacy-empty")
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert (
        ReportValue["source_sha256"]
        == "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408"
    )
    assert ReportValue["output_bytes"] > 0
    assert ReportValue["status"] is None
    assert ReportValue["unsupported"] == (
        "SOLIDWORKS part text properties are unavailable for strict cross-format conversion"
    )
    assert ReportValue["binary_refusal"] == ReportValue["unsupported"]
    assert ReportValue["binary_diagnostic"] == (
        "part property manager has unsupported owner placement"
    )
