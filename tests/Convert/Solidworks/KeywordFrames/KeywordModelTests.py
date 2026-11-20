from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.MakeKeyWire import (
    KKeywordName,
    KKeywordTail,
    KKeywordText,
    MakeKeyWire,
)
from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# compaction must preserve the authored text and attribute values through parsing
def TestKeyXml(TmpPath: FilePath) -> None:
    for StyleName, IsCompact in (("Compact", True), ("Spaced", False)):
        AuthoredPath = TmpPath / f"{StyleName}.json"
        WirePath = TmpPath / f"{StyleName}.bin"
        ReadPath = TmpPath / f"{StyleName}-read.json"
        Fields = {
            "root": "Keywords",
            "name": KKeywordName,
            "text": KKeywordText,
            "tail": KKeywordTail,
        }
        _ = AuthoredPath.write_text(
            DumpJson({**Fields, "compact": IsCompact}), encoding="utf-8"
        )
        Written = RunKeywordFrame("write", AuthoredPath, WirePath)
        assert Written.returncode == 0, Written.stdout + Written.stderr
        assert WirePath.read_bytes() == MakeKeyWire(IsCompact)
        Outcome = RunKeywordFrame("read", WirePath, ReadPath)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        assert LoadJson(ReadPath.read_text(encoding="utf-8")) == Fields
