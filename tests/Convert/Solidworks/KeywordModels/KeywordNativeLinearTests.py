from hashlib import sha256 as MakeDigest
from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordModels.RunKeywordModel import RunKeyModel

# the native control supplies source bytes to the reader and never to the writer
KLinearControl = (
    FilePath(__file__).resolve().parents[4]
    / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"
)


# separated reader and writer processes must preserve the complete compact native index
def TestNativeLinearKeywords() -> None:
    Projected = RunKeyModel("project-linear", KLinearControl.read_bytes())
    assert Projected.returncode == 0, Projected.stderr
    Emitted = RunKeyModel("write", Projected.stdout)
    assert Emitted.returncode == 0, Emitted.stderr
    assert len(Emitted.stdout) == 1739
    assert (
        MakeDigest(Emitted.stdout).hexdigest()
        == "507f9c7c1b6c4a70ea1ab7fe4c3e66b4cbab6f46168dc5e1338c5710499a69ef"
    )
    ReadBack = RunKeyModel("read", Emitted.stdout)
    assert ReadBack.returncode == 0, ReadBack.stderr
    Report = LoadJson(ReadBack.stdout)
    assert Report["dissectable"] == [["26", "true"]]
    assert Report["dimensions"] == [
        ["34", [["D1", "10"]]],
        ["26", [["D1", "40"], ["D2", "20"]]],
    ]
