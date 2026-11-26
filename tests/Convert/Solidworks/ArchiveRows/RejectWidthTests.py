from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveRows.RunRows import RunRows


# a width constraint needs a compatible word and cannot bypass an invalid mode
def TestBadWidths(TmpPath: FilePath) -> None:
    EmptyRows: dict[str, list[dict[str, int]]] = {
        NameValue: []
        for NameValue in (
            "rows",
            "framework_rows",
            "signed_rows",
            "split_rows",
            "combined_rows",
        )
    }
    for LabelName, WordsValue, OptionsValue, ErrorText in (
        ("VendorWidth", {"row_count": 0, "row_count#width": 14}, (), "count width"),
        (
            "NarrowWidth",
            {"framework_rows#count": 65535, "framework_rows#count#width": 2},
            (),
            "count width",
        ),
        ("MissingWord", {"row_count#width": 6}, (), "count width"),
        (
            "InvalidMode",
            {"row_count": -1},
            ("--count-mode", "Unsupported"),
            "unsupported native array count mode",
        ),
    ):
        SourcePath = TmpPath / f"{LabelName}.json"
        WirePath = TmpPath / f"{LabelName}.bin"
        _ = SourcePath.write_text(
            DumpJson({**EmptyRows, **WordsValue}), encoding="utf-8"
        )
        Outcome = RunRows("write", SourcePath, WirePath, OptionsValue)
        assert Outcome.returncode != 0
        assert ErrorText in Outcome.stderr
        assert not WirePath.exists()
