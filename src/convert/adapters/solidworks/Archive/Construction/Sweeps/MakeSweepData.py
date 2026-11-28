from convert.adapters.solidworks.Archive.Construction.Sweeps.Refs.MakeSwContact import (
    MakeSwContact,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepObjectRows import (
    MakeSweepRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# standard solid sweep starts with the actual section and path and no solved result state
def MakeSweepData(
    SectionValue: ArchiveNode, PathValue: ArchiveNode
) -> dict[str, object]:
    return {
        "f2c0": MakeSweepRows(SectionValue),
        "f2e0": MakeSweepRows(MakeSwContact(PathValue)),
        "f300": MakeSweepRows(),
        "f270": 0,
        "f274": 0,
        "f278": 0,
        "f70": 1.0,
        "f2ac": 0,
        "f2b0": 0,
        "f7c": 0,
        "f80": 0,
        "f98": MakeSweepRows(),
        "fe0": MakeSweepRows(),
        "f230": 0,
        "f78": 0,
        "f234": 0,
        "f238": 0.0,
        "f240": 0.0,
        "f248": 0,
        "f24c": 1,
        "f2b4": 0,
        "f280": 0.0,
        "f288": 0.0,
        "f290": 0,
        "f27c": 0,
        "f2a8": 0,
        "f258": 0,
        "f260": 0.0,
        "f298": None,
        "f2a0": None,
        "f2b8": 0,
        "f320": MakeSweepRows(),
        "f340": MakeSweepRows(),
        "f3b0": 0,
    }
