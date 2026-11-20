from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# tag names must retain their boundaries before either framing mode publishes output
def TestTagNames(TmpPath: FilePath) -> None:
    for IndexValue, ChildTag in enumerate(("Dimension\r", "Dimension ", "!--", "?pi")):
        for CompactMode in (True, False):
            Source = TmpPath / f"tag{IndexValue}{CompactMode}.json"
            Output = Source.with_suffix(".bin")
            _ = Source.write_text(
                DumpJson(
                    {
                        "root": "Keywords",
                        "compact": CompactMode,
                        "name": "Part",
                        "text": "child",
                        "tail": "after",
                        "child_tag": ChildTag,
                    }
                ),
                encoding="utf-8",
            )
            Outcome = RunKeywordFrame("write", Source, Output)
            assert Outcome.returncode != 0
            assert "requires well-formed XML names" in Outcome.stderr
            assert not Output.exists()
