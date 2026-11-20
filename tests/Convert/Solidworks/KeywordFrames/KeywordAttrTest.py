from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# a qualified attribute value keeps its own namespace even when the element name is unqualified
def TestQNameAttr(TmpPath: FilePath) -> None:
    for Scenario in ("ordinary", "shadow", "invalid"):
        Source = TmpPath / f"attribute{Scenario}.json"
        Target = Source.with_suffix(".bin")
        _ = Source.write_text(
            DumpJson(
                {
                    "root": "Keywords",
                    "compact": True,
                    "name": "Part",
                    "text": "",
                    "tail": "",
                    "qualified_attribute": True,
                    "qualified_attribute_shadow": Scenario == "shadow",
                    "invalid_qualified_attribute": Scenario == "invalid",
                }
            ),
            encoding="utf-8",
        )
        Result = RunKeywordFrame("write", Source, Target)
        if Scenario != "ordinary":
            assert Result.returncode != 0
            assert not Target.exists()
        else:
            assert Result.returncode == 0, Result.stdout + Result.stderr
            PayloadValue = Target.read_bytes()
            assert b'xmlns:ns0="urn:kit:keyword"' in PayloadValue
            assert b'state="ns0:Native"' in PayloadValue
