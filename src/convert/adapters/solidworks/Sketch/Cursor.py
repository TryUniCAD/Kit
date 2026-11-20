from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    KDistanceRow,
    KEntityHandle,
    SketchReference,
)
from convert.adapters.solidworks.Sketch.MemberSpans import DistanceSpan

# the full circle and the primary point adjacency share this allocated handle type
KCircleHandle = "sgArcHandle"


# sketch local operand data shares its ownership map with the enclosing feature
class SketchArchive(ArchiveCursor):
    KCircularHandles: bool = False

    # local handles need an independent state while their allocations stay with the owner
    def __init__(self, Parent: ArchiveCursor) -> None:
        super().__init__(
            Parent.BlobValue,
            Parent.Offset,
            Parent.NextIndex,
            Parent.Classes,
            Parent.Objects,
        )
        self.PointerEvents = Parent.PointerEvents
        self.NodeNames: dict[int, str] = {}
        self.Scalars: dict[int, tuple[str, float]] = {}
        self.ScalarOffsets: dict[int, int] = {}
        self.Dimensions: list[tuple[KDistanceRow, DistanceSpan]] = []
        self.Handles: dict[int, KEntityHandle] = {}
        self.SketchReferences: dict[int, SketchReference] = {}
        self.PointReferences: dict[int, SketchReference] = {}

    # new local objects must consume their own fields before later aliases can resolve
    def ReadObject(self, *Expected: str | None) -> int:
        if self.KCircularHandles and Expected == (None, "sgLineHandle"):
            Expected = (None, KCircleHandle)
        TagValue, NameValue, ObjectIndex = self.TakePointer(Expected)
        if NameValue is not None and TagValue.kind in (KDefinitionKind, KClassRefKind):
            self.ReadPayload(NameValue, ObjectIndex)
        return ObjectIndex

    # layouts outside the normal sketch scope must fail at their typed boundary
    def ReadPayload(self, NameValue: str, ObjectIndex: int) -> None:
        from convert.adapters.solidworks.Sketch.Objects import ReadSketchMut

        if self.KCircularHandles and NameValue in (KCircleHandle, "sgEntHandle"):
            ReadArcSlotMut(self, NameValue, ObjectIndex)
            return
        ReadSketchMut(self, NameValue, ObjectIndex)


# the radial adjacency and inactive operand use different native widths and owner invariants
def ReadArcSlotMut(Cursor: SketchArchive, NameValue: str, ObjectIndex: int) -> None:
    if NameValue == KCircleHandle:
        (SlotValue,) = Cursor.ReadInts("<H")
        RequireArch(SlotValue < 0x777F, True, "unsupported circular handle index width")
        Owner, Flags = Cursor.ReadInts("<2i")
    else:
        RequireArch(
            Cursor.ReadInts("<H") == (0x777F,),
            True,
            "expected invalid placeholder index width",
        )
        SlotValue, Owner, Flags = Cursor.ReadInts("<3i")
        RequireArch(SlotValue == -2, True, "unexpected second G1 operand")
    RequireArch((Owner, Flags) == (-1, 0), True, "circular handle is not local")
    Cursor.Handles[ObjectIndex] = SlotValue, Owner, Flags
