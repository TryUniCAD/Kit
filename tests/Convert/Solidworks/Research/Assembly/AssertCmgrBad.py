from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from tests.Convert.Solidworks.Research.Assembly.RunCmgrCheck import RunCmgrCheck


# malformed complete files must reject their typed manager without publishing a successful receipt
def AssertCmgrBad(ParentPath: FilePath) -> None:
    Archive = SldprtArchive.from_bytes(ParentPath.read_bytes())
    CmgrBytes = Archive.require("Contents/CMgr")
    ClassName = b"moConfigurationMgr_c"
    assert CmgrBytes.count(ClassName) == 1
    for Label, BufferValue, Message in (
        ("ShortManager", CmgrBytes[:-1], "truncated SOLIDWORKS archive field"),
        (
            "UnknownManager",
            CmgrBytes.replace(ClassName, b"moUnsupportedClass_c"),
            "unsupported SOLIDWORKS body class",
        ),
    ):
        Streams = dict(Archive.streams)
        Streams["Contents/CMgr"] = BufferValue
        BrokenPath = ParentPath.with_stem(Label)
        with BrokenPath.open("xb") as Output:
            _ = Output.write(build_sldprt(Streams))
        ReportPath = BrokenPath.with_suffix(".json")
        Outcome = RunCmgrCheck((BrokenPath,), ReportPath)
        assert Outcome.returncode != 0 and Message in Outcome.stderr
        assert not ReportPath.exists()
        Document = OpenDocument(
            BrokenPath, include_brep=False, include_tessellation=False
        )
        InfoValue = CastValue(
            dict[str, object],
            Document.metadata["solidworks.typed_configuration_manager"],
        )
        assert (
            InfoValue["status"] == "unsupported"
            and InfoValue["full_linked_graph"] is False
        )
        assert Message in str(InfoValue["diagnostic"])
        UsageValue = CastValue(dict[str, object], InfoValue["usage"])
        assert UsageValue["completed"] is False
        assert any(
            ItemValue.code == "solidworks.typed_configuration_manager_unavailable"
            for ItemValue in Document.diagnostics
        )
