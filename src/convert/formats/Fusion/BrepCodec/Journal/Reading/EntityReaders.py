from collections.abc import Callable

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadAttribNode import (
    ReadAttribNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadAsmRoot import (
    ReadAsmRoot,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadBodyNode import (
    ReadBodyNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadLumpNode import (
    ReadLumpNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadShellNode import (
    ReadShellNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadFaceNode import (
    ReadFaceNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadLoopNode import (
    ReadLoopNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadCoedgeNode import (
    ReadCoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadEdgeNode import (
    ReadEdgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadVertexNode import (
    ReadVertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadPointNode import (
    ReadPointNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadPlaneNode import (
    ReadPlaneNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadEllipseNode import (
    ReadEllipseNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadConeNode import (
    ReadConeNode,
)

from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadStraight import (
    ReadStraight,
)

from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadTransform import (
    ReadTransform,
)

KEntityReaders: dict[str, Callable[[FieldCursor], KJournalEntity]] = {
    "straight-curve": ReadStraight,
    "transform": ReadTransform,
    "asmheader": ReadAsmRoot,
    "body": ReadBodyNode,
    "lump": ReadLumpNode,
    "shell": ReadShellNode,
    "face": ReadFaceNode,
    "loop": ReadLoopNode,
    "coedge": ReadCoedgeNode,
    "edge": ReadEdgeNode,
    "vertex": ReadVertexNode,
    "point": ReadPointNode,
    "plane-surface": ReadPlaneNode,
    "ellipse-curve": ReadEllipseNode,
    "cone-surface": ReadConeNode,
    "ATTRIB_CUSTOM-attrib": ReadAttribNode,
}
