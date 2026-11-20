from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Sketch.DimHandle import ReadRefTail
from convert.adapters.solidworks.Sketch.Objects import KDistanceTypes, KProxyTypes
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    KDistanceRow,
    KEntityHandle,
    SketchReference,
)
from convert.adapters.solidworks.Sketch.MemberSpans import DistanceSpan, MemberSpan

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


# proxy targets are usable only after the local part and entity handle resolve
def ReadLocalRefMut(Cursor: SketchArchive, ObjectIndex: int) -> None:
    _ = ReadLocalPart(Cursor, KConfigGen)
    FeatureId, TimeWord = Cursor.ReadInts("<iI")
    RequireArch(TimeWord < 0xFFFFFFFF, True, "compact feature reference time")
    Entity = Cursor.ReadObject("sgPointHandle", "sgLineHandle")
    Cursor.SketchReferences[ObjectIndex] = {
        "feature_id": FeatureId,
        "feature_time": TimeWord,
        "handle_class": Cursor.Objects[Entity],
        "handle_fields": Cursor.Handles[Entity],
    }
    _ = Cursor.ReadInts("<I")


# proxy wrappers preserve the target identity independently of their later display values
def ReadProxyMut(Cursor: SketchArchive, NameValue: str, ObjectIndex: int) -> None:
    if NameValue == "sgExtEnt_c":
        Wrapper = Cursor.ReadObject("moSketchExtRef_w")
        Cursor.SketchReferences[ObjectIndex] = Cursor.SketchReferences[Wrapper]
        for _ in range(3):
            _ = Cursor.ReadObject(None)
        _ = Cursor.ReadText()
    elif NameValue == "moSketchExtRef_w":
        Component = Cursor.ReadObject("moCompSketchEntHandle_c")
        Cursor.SketchReferences[ObjectIndex] = Cursor.SketchReferences[Component]
        ReadRefTail(Cursor)
        (Flags,) = Cursor.ReadInts("<h")
        RequireArch(-2 <= Flags <= 0, True, "valid external reference mode")
        _ = Cursor.ReadObject(None, "moPointBackedUpData_c")
    else:
        ReadLocalRefMut(Cursor, ObjectIndex)


# length values need their own saved node names before dimensions can bind them
def ReadLengthMut(Cursor: SketchArchive, ObjectIndex: int) -> None:
    NameIndex = Cursor.ReadObject("moNodeName_c")
    _ = Cursor.ReadInts("<4i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadObject(None)
    Offset = Cursor.Offset
    (Value,) = Cursor.ReadPoint(1)
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent native length override")
    NameValue = Cursor.NodeNames.get(NameIndex)
    if NameValue is None:
        raise ArchiveError("unbound local length parameter name")
    Cursor.Scalars[ObjectIndex] = NameValue, Value
    Cursor.ScalarOffsets[ObjectIndex] = Offset


# unsupported object classes must be rejected before their body can move the cursor
def ReadSketchMut(Cursor: SketchArchive, NameValue: str, ObjectIndex: int) -> None:
    if NameValue in ("sgPointHandle", "sgLineHandle"):
        (Index,) = Cursor.ReadInts("<H")
        RequireArch(Index < 0x777F, True, "short sketch handle index width")
        Owner, Flags = Cursor.ReadInts("<2i")
        Cursor.Handles[ObjectIndex] = Index, Owner, Flags
    elif NameValue in KProxyTypes:
        ReadProxyMut(Cursor, NameValue, ObjectIndex)
    elif NameValue == "moPointBackedUpData_c":
        _ = Cursor.ReadPoint(3)
    elif NameValue == "moNodeName_c":
        Cursor.NodeNames[ObjectIndex] = Cursor.ReadText()
    elif NameValue == "moLengthParameter_c":
        ReadLengthMut(Cursor, ObjectIndex)
    elif NameValue in KDistanceTypes:
        ReadDistanceMut(Cursor, NameValue)
    else:
        raise ArchiveError(
            f"Unsupported materialization of {NameValue} at {Cursor.Offset}"
        )


# display and sketch dimensions share the stored parameter reference and activity state
def ReadDimFields(
    Cursor: SketchArchive, ExpectedParam: str | None
) -> tuple[int, int, int]:
    _ = Cursor.ReadInts("<i")
    ValueId = Cursor.ReadObject(ExpectedParam)
    _ = Cursor.ReadObject(None)
    DimId, _, _, _ = Cursor.ReadInts("<4i")
    _ = Cursor.ReadObject(None)
    (State,) = Cursor.ReadInts("<H")
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent dimension alternate name")
    return DimId, ValueId, State


# local dimension types follow the parameter fields and determine their operand interpretation
def ReadDimBase(
    Cursor: SketchArchive, ExpectedParam: str | None
) -> tuple[int, int, int]:
    DimId, ValueId, _ = ReadDimFields(Cursor, ExpectedParam)
    TypeValue, *_ = Cursor.ReadInts("<i3H")
    return DimId, ValueId, TypeValue


# the distance and both native operands must belong to the same dimension object
def ReadDistanceMut(Cursor: SketchArchive, ClassName: str) -> None:
    Start = Cursor.Offset
    DimId, ValueId, State = ReadDimFields(Cursor, "moLengthParameter_c")
    TypeValue, OperandCount, Deleted, Reserved = Cursor.ReadInts("<i3H")
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent sgValGDim transform")
    First = Cursor.ReadObject("sgPointHandle")
    Second = Cursor.ReadObject("sgPointHandle")
    _ = Cursor.ReadInts("<4H")
    _ = Cursor.ReadObject(None)
    _ = Cursor.ReadPoint(3)
    Label, Metres = Cursor.Scalars[ValueId]
    Source = DistanceSpan(
        MemberSpan(Start, Cursor.Offset),
        Cursor.ScalarOffsets[ValueId],
        TypeValue,
        (State, OperandCount, Deleted, Reserved) == (0, 2, 0, 0),
    )
    Cursor.Dimensions.append(((ClassName, DimId, Label, Metres, First, Second), Source))
