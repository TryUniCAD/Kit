from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.Properties.RunPartText import KPartCorpus


# the public decode envelope must keep identically named properties in their authored scopes
def TestScopeText(TmpPath: FilePath) -> None:
    Source = KPartCorpus / "part-properties/CircularProperties.SLDPRT"
    Result = CliProcess(
        TmpPath, "decode", str(Source), "--configuration", "modeled default"
    )
    assert Result.returncode == 0, Result.stderr
    Decoded = LoadJson(Result.stdout)
    assert Decoded["layer"] == "neutral" and Decoded["partial"] is False
    Document = Decoded["document"]
    (Configuration,) = Document["configurations"]["$tuple"]
    assert Configuration["name"] == "modeled default"
    assert Configuration["active"] is True
    assert Document["metadata"]["custom_properties"] == {
        "KitBatch": "Run B7 & B8",
        "KitMaterialNote": "Ring stock β",
        "KitRevision": 'fit "R2" <limit>',
    }
    assert Configuration["attributes"]["custom_properties"] == {
        "KitRevision": 'Configuration "Q4"',
        "KitSetting": "Diameter option",
    }
