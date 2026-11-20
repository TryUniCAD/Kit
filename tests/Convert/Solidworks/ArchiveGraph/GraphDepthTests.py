from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveGraph.MakeDepthWire import MakeDepthWire
from tests.Convert.Solidworks.ArchiveGraph.RunGraph import RunGraph


# terminal references must resolve exactly where another nested body would fail
def TestGraphDepth(TmpPath: FilePath) -> None:
    for LabelName, BodyCount, AddsClass in (
        ("DepthLimit", 128, False),
        ("DeepReference", 129, False),
        ("DeepNewClass", 129, True),
    ):
        InputRoot = TmpPath / LabelName
        InputRoot.mkdir()
        PrimaryValue, LinkedValue = MakeDepthWire(BodyCount, AddsClass)
        _ = (InputRoot / "Primary.bin").write_bytes(PrimaryValue)
        _ = (InputRoot / "Linked.bin").write_bytes(LinkedValue)
        ReportPath = TmpPath / f"{LabelName}.json"
        Outcome = RunGraph("read", InputRoot, ReportPath)
        if BodyCount == 129:
            assert Outcome.returncode != 0
            assert (
                "SOLIDWORKS archive nesting exceeds the supported depth"
                in Outcome.stderr
            )
            assert not ReportPath.exists()
            continue
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        GraphValue = LoadJson(ReportPath.read_text(encoding="utf-8"))
        assert GraphValue["primary"]["next"] == 131
        assert GraphValue["linked"] == {"root": 131, "base": 131, "next": 132}
        assert GraphValue["objects"][-2:] == [
            [130, "Leaf", 29, [2, None]],
            [131, "Leaf", 41, [130, 2]],
        ]
