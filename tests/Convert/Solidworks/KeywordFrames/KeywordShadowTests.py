from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# a literal descendant declaration must not change an expanded name before publication
def TestNsShadow(TmpPath: FilePath) -> None:
    for CompactMode in (True, False):
        Source = TmpPath / f"shadow{CompactMode}.json"
        Output = Source.with_suffix(".bin")
        _ = Source.write_text(
            DumpJson(
                {
                    "root": "Keywords",
                    "compact": CompactMode,
                    "name": "Part",
                    "text": "child",
                    "tail": "after",
                    "namespace_shadow": True,
                }
            ),
            encoding="utf-8",
        )
        Written = RunKeywordFrame("write", Source, Output)
        assert Written.returncode != 0
        assert "requires well-formed XML" in Written.stderr
        assert not Output.exists()
