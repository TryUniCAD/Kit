from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveGraph.AuthoredGraph import AuthoredGraph
from tests.Convert.Solidworks.ArchiveGraph.ExpectedGraph import ExpectedGraph
from tests.Convert.Solidworks.ArchiveGraph.ExpectedWire import ExpectedWire
from tests.Convert.Solidworks.ArchiveGraph.RunGraph import RunGraph


# the complete process pair must prove wire bytes as well as inherited graph identity
def TestGraph(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Authored.json"
    OutputRoot = TmpPath / "Streams"
    ReportPath = TmpPath / "Graph.json"
    OutputRoot.mkdir()
    _ = SourcePath.write_text(DumpJson(AuthoredGraph()), encoding="utf-8")
    WriteResult = RunGraph("write", SourcePath, OutputRoot)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert (
        (OutputRoot / "Primary.bin").read_bytes(),
        (OutputRoot / "Linked.bin").read_bytes(),
    ) == ExpectedWire()
    ReadResult = RunGraph("read", OutputRoot, ReportPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReportPath.read_text(encoding="utf-8")) == ExpectedGraph()
