from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# the actual root mode and document boundary must qualify before publishing any framed bytes
def TestBadKeys(TmpPath: FilePath) -> None:
    for CaseName, RootValue, ModeValue, TailValue, Diagnostic in (
        ("WrongRoot", "KeyWords", True, None, "requires the actual keyword root"),
        ("WrongMode", "Keywords", 1, None, "requires the actual keyword root"),
        (
            "RootTail",
            "Keywords",
            True,
            "\r\n",
            "requires content inside the keyword root",
        ),
    ):
        SourcePath = TmpPath / f"{CaseName}.json"
        WirePath = TmpPath / f"{CaseName}.bin"
        _ = SourcePath.write_text(
            DumpJson(
                {
                    "root": RootValue,
                    "compact": ModeValue,
                    "name": "a",
                    "text": "b",
                    "tail": "c",
                    "root_tail": TailValue,
                }
            ),
            encoding="utf-8",
        )
        Outcome = RunKeywordFrame("write", SourcePath, WirePath)
        assert Outcome.returncode != 0
        assert Diagnostic in Outcome.stderr
        assert not WirePath.exists()
