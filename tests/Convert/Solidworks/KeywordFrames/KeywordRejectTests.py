from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# root and mode validation must occur before publishing any framed bytes
def TestBadKeys(TmpPath: FilePath) -> None:
    for CaseName, RootValue, ModeValue in (
        ("WrongRoot", "KeyWords", True),
        ("WrongMode", "Keywords", 1),
    ):
        SourcePath = TmpPath / f"{CaseName}.json"
        WirePath = TmpPath / f"{CaseName}.bin"
        _ = SourcePath.write_text(
            DumpJson(
                {"root": RootValue, "compact": ModeValue, "name": "a", "text": "b"}
            ),
            encoding="utf-8",
        )
        Outcome = RunKeywordFrame("write", SourcePath, WirePath)
        assert Outcome.returncode != 0
        assert "keyword framing requires the actual keyword root" in Outcome.stderr
        assert not WirePath.exists()
