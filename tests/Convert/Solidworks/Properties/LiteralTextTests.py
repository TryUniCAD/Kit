from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

# the disclosed native save is a read fixture with independently measured text
KFixture = (
    FilePath(__file__).resolve().parents[4]
    / "re/solidworks/v2026/corpus/part-properties/CircularProperties.SLDPRT"
)

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


# the queue checks all three native text scopes through the ordinary sdk process
def TestLiteralText() -> None:
    WorkerPath = FilePath(__file__).with_name("ReadLiteralPart.py")
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(WorkerPath), str(KFixture)),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert (
        ReportValue["source_sha256"]
        == "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23"
    )
    assert ReportValue["status"]["status"] == "complete"
    assert ReportValue["status"]["configuration_ids"] == [0]
    assert ReportValue["text"] == KNativeText
    assert ReportValue["configuration"] == ["modeled default", True, 0]
    assert ReportValue["body"] == ["sldprt:body:1", 1, 1, 1]
