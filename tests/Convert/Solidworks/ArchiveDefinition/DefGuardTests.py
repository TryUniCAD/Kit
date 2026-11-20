from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.ArchiveDefinition.RunDefProcess import RunDefProcess


# queue coverage must keep actual unsupported definition profiles from reaching serialization
def TestDefRefusals(TmpPath: FilePath) -> None:
    Report = CastValue(
        dict[str, str], LoadJson(RunDefProcess(TmpPath, "refusals", b""))
    )
    assert set(Report) == {
        "read_assembly",
        "read_old_version",
        "read_tail",
        "write_assembly",
        "write_future_version",
        "write_invalid_display_bits",
        "write_model_data_scene",
        "write_renderer_inactive",
        "write_renderer_marker",
        "write_renderer_objects",
        "write_root_schema",
        "write_unknown_density",
    }
    assert "renderer objects" in Report["write_renderer_objects"]
    assert "alternate scene or OLE owner" in Report["write_model_data_scene"]


# ordinary definition replay needs physical tag widths that its writer can reproduce
def TestDefWideTags(TmpPath: FilePath) -> None:
    WireValue = RunDefProcess(TmpPath, "author_refs", b"")
    Report = CastValue(
        dict[str, str], LoadJson(RunDefProcess(TmpPath, "wide_refs", WireValue))
    )
    assert set(Report) == {"ObjectRef", "ClassRef"}
    assert all(
        "archive tag uses a noncanonical width" in Diagnostic
        for Diagnostic in Report.values()
    )


# the first escaped slot distinguishes replay support from blanket rejection
def TestDefWideRead(TmpPath: FilePath) -> None:
    WireValue = RunDefProcess(TmpPath, "author_wide_tag", b"")
    Report = CastValue(
        dict[str, object],
        LoadJson(RunDefProcess(TmpPath, "replay_wide_tag", WireValue)),
    )
    assert Report == {
        "object_index": 0x7FFF,
        "next_map_index": 0x8004,
        "tag_width": 6,
        "typed_wire_equal": True,
    }


# an extra class declaration would shift subsequent object slots during replay
def TestDefClass(TmpPath: FilePath) -> None:
    WireValue = RunDefProcess(TmpPath, "author_refs", b"")
    Report = CastValue(
        dict[str, object],
        LoadJson(RunDefProcess(TmpPath, "repeat_type_declaration", WireValue)),
    )
    assert Report["class_name"] == "moLineStyle_c"
    assert Report["canonical_class_slot"] == 3
    assert Report["canonical_replays"] is True
    assert "archive repeats a canonical class declaration" in CastValue(
        str, Report["diagnostic"]
    )
