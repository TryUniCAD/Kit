from convert.Geometry.Parasolid import EncodePartData
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeEmptyWorld import (
    MakeEmptyWorld,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.BindGhostShape import (
    BindGhostShape,
    GhostPlacement,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSweepXmt import (
    EncodeSweepXmt,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeGhostAttrib import (
    MakeGhostDefs,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the computed ghost partition starts with one world and the attributed wire followed by the attributed sheet
def MakeGhostWorld(
    SheetValue: tuple[XmtNode, ...],
    WireValue: tuple[XmtNode, ...],
    SectionId: int,
    PathId: int,
) -> bytes:
    WorldValue = MakeEmptyWorld(1, 1, len((SectionId, PathId)))
    BodySchema, EdgeSchema, *TextValues = MakeGhostDefs(WorldValue.IndexValue + 1)
    PathIndex = TextValues[-1].IndexValue + 1
    SectionIndex = PathIndex + len(WireValue) + 5
    PathValues = BindGhostShape(
        WireValue,
        GhostPlacement(
            PathIndex,
            SectionIndex,
            0,
            WorldValue.IndexValue,
            BodySchema.IndexValue,
            EdgeSchema.IndexValue,
            PathId,
        ),
    )
    SectionValues = BindGhostShape(
        SheetValue,
        GhostPlacement(
            SectionIndex,
            0,
            PathIndex,
            WorldValue.IndexValue,
            BodySchema.IndexValue,
            EdgeSchema.IndexValue,
            SectionId,
        ),
    )
    WorldValue = XmtNode(
        WorldValue.IndexValue,
        WorldValue.KindValue,
        dict(WorldValue.FieldsValue)
        | {
            "attrib_def": BodySchema.IndexValue,
            "body": PathIndex,
        },
    )
    NodesValue = (
        WorldValue,
        BodySchema,
        EdgeSchema,
        *TextValues,
        *PathValues,
        *SectionValues,
    )
    return EncodePartData(EncodeSweepXmt(NodesValue, True))
