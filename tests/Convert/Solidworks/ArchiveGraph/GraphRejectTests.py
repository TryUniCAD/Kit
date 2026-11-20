from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveGraph.ExpectedWire import ExpectedWire
from tests.Convert.Solidworks.ArchiveGraph.RunGraph import RunGraph


# map kind and seed failures must prevent publication of a partially resolved graph
def TestBadGraph(TmpPath: FilePath) -> None:
    PrimaryValue, LinkedValue = ExpectedWire()
    for LabelName, Primary, Linked, ErrorText in (
        (
            "ClassSlot",
            PrimaryValue[:-2] + b"\x01\x00",
            LinkedValue,
            "wrong kind archive object reference 1",
        ),
        (
            "WrongBase",
            PrimaryValue,
            b"\x07\x00\x00\x00" + LinkedValue[4:],
            "archive map seed counter differs from the stream base",
        ),
    ):
        InputRoot = TmpPath / LabelName
        InputRoot.mkdir()
        _ = (InputRoot / "Primary.bin").write_bytes(Primary)
        _ = (InputRoot / "Linked.bin").write_bytes(Linked)
        ReportPath = TmpPath / f"{LabelName}.json"
        Outcome = RunGraph("read", InputRoot, ReportPath)
        assert Outcome.returncode != 0
        assert ErrorText in Outcome.stderr
        assert not ReportPath.exists()
