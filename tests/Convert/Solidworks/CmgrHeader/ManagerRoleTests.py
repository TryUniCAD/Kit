from json import dumps as DumpJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.CmgrHeader.MakeMgrDesc import MakeMgrDesc
from tests.Convert.Solidworks.CmgrHeader.RunMgrWire import RunMgrWire


# an incorrect descriptor must fail even when its putative body is absent
def TestWrongRole(TmpPath: FilePath) -> None:
    RootPrefix = MakeMgrDesc("dmConfigMgrHeader_c")
    for LabelName, BodyValue, ExpectedType in (
        ("Root", MakeMgrDesc("dmConfigHeader_c"), "dmConfigMgrHeader_c"),
        ("Nested", RootPrefix + PackValues("<HH", 1, 0x8001), "dmConfigHeader_c"),
        (
            "Schema",
            RootPrefix + PackValues("<H", 1) + MakeMgrDesc("dmConfigHeader_c", 2),
            "dmConfigHeader_c",
        ),
    ):
        WirePath = TmpPath / f"{LabelName}.bin"
        ReportPath = TmpPath / f"{LabelName}.json"
        _ = WirePath.write_bytes(BodyValue)
        Outcome = RunMgrWire("read", WirePath, ReportPath)
        assert Outcome.returncode != 0
        ErrorText = f"expected {ExpectedType} schema 1 before reading its body"
        assert ErrorText in Outcome.stderr
        assert not ReportPath.exists()


# null or manager aliases cannot serve as configuration header rows
def TestBadLinks(TmpPath: FilePath) -> None:
    RootPrefix = MakeMgrDesc("dmConfigMgrHeader_c")
    for LabelName, TagValue, RowValue in (("Null", 0, None), ("Manager", 2, "root")):
        WirePath = TmpPath / f"{LabelName}.bin"
        SourcePath = TmpPath / f"{LabelName}.json"
        _ = WirePath.write_bytes(RootPrefix + PackValues("<HHIi", 1, TagValue, 77, 1))
        _ = SourcePath.write_text(
            DumpJson({"saved_at": 77, "sort_word": 1, "rows": [RowValue]}),
            encoding="utf-8",
        )
        for ModeName, InputPath in (("read", WirePath), ("write", SourcePath)):
            ResultPath = TmpPath / f"{LabelName}-{ModeName}.out"
            Outcome = RunMgrWire(ModeName, InputPath, ResultPath)
            assert Outcome.returncode != 0
            assert (
                "directory row requires a concrete configuration header"
                in Outcome.stderr
            )
            assert not ResultPath.exists()
