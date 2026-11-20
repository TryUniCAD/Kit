from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# forbidden xml characters must fail before either lexical form publishes output
def TestInvalidXmlCharacters(TmpPath: FilePath) -> None:
    for FieldName in ("name", "text", "tail"):
        for IndexValue, CharacterValue in enumerate(("\x00", "\x01", "\ud800")):
            for CompactMode in (True, False):
                Source = TmpPath / f"{FieldName}{IndexValue}{CompactMode}.json"
                Output = Source.with_suffix(".bin")
                Values = {"name": "Part", "text": "child", "tail": "after"}
                Values[FieldName] += CharacterValue
                _ = Source.write_text(
                    DumpJson({"root": "Keywords", "compact": CompactMode, **Values}),
                    encoding="utf-8",
                )
                Outcome = RunKeywordFrame("write", Source, Output)
                assert Outcome.returncode != 0
                assert "requires well-formed XML" in Outcome.stderr
                assert not Output.exists()


# the serialized document must preserve names and remain valid after carriage return encoding
def TestInvalidKeywordNames(TmpPath: FilePath) -> None:
    for IndexValue, ChildTag in enumerate(("Dimension\r", "Dimension ")):
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
            assert "requires well-formed XML" in Outcome.stderr
            assert not Output.exists()
