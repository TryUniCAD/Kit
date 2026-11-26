from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.ArchiveDefinition.RunDefProcess import (
    KRepoRoot,
    RunDefProcess,
)

# the tracked ladder part supplies an immutable native regression control
KLadderPart = KRepoRoot / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"


# the populated part definition must preserve its map and emit the same wire bytes
def TestDefReplay(TmpPath: FilePath) -> None:
    SourceBytes = KLadderPart.read_bytes()
    Report = CastValue(
        dict[str, object], LoadJson(RunDefProcess(TmpPath, "L1", SourceBytes))
    )
    assert Report["file_sha256"] == (
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
    )
    assert Report["sha256"] == (
        "14d9b75edf4586f8e1db2b166e855e29a03d4c88256e26d24351edb5c43d8a87"
    )
    assert Report["size"] == 3816 and Report["next_map_index"] == 60
    assert Report["root"] == ["uiPartDoc_c", 1] and Report["typed_wire_equal"] is True
    assert Report["line_style_count"] == 7 and Report["font_count"] == 40
    assert Report["splitter_grids"] == [[[1, 1], [2, 1]]]
    assert Report["renderer_empty_wrapper"] == [6, 0, 0]
    assert KLadderPart.read_bytes() == SourceBytes
