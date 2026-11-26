from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# equivalent named element forms must serialize identically through the xml encoder
def TestQName(TmpPath: FilePath) -> None:
    Outputs: list[bytes] = []
    for NameKind in ("object", "expanded"):
        Source = TmpPath / f"{NameKind}.json"
        Target = TmpPath / f"{NameKind}.bin"
        _ = Source.write_text(
            DumpJson(
                {
                    "root": "Keywords",
                    "compact": True,
                    "name": "Part",
                    "text": "",
                    "tail": "",
                    "qualified": NameKind,
                }
            ),
            encoding="utf-8",
        )
        Result = RunKeywordFrame("write", Source, Target)
        assert Result.returncode == 0, Result.stdout + Result.stderr
        Outputs.append(Target.read_bytes())
    assert Outputs[0] == Outputs[1]
    assert b"<ns0:Native/>" in Outputs[0]
