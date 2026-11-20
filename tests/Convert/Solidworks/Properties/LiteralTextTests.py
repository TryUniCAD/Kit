from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Properties.RunPartText import KPartCorpus, RunPartText

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
    ReportValue = RunPartText(
        FilePath(__file__).with_name("ReadLiteralPart.py"),
        KPartCorpus / "part-properties/CircularProperties.SLDPRT",
    )
    StatusValue = CastValue(dict[str, object], ReportValue["status"])
    assert (
        ReportValue["source_sha256"]
        == "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23"
    )
    assert StatusValue["status"] == "complete"
    assert StatusValue["configuration_ids"] == [0]
    assert ReportValue["text"] == KNativeText
    assert ReportValue["text_scopes"] == [True, True, True]
    assert ReportValue["configuration"] == ["modeled default", True, 0]
    assert ReportValue["body"] == ["sldprt:body:1", 1, 1, 1]
