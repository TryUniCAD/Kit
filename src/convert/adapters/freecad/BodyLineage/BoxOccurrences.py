from dataclasses import dataclass as MakeDataClass
from hashlib import sha256 as HashBytes

from convert.adapters.freecad.BodyLineage.BoxLineage import KBoxKind
from convert.adapters.freecad.BodyLineage.BoxPrismRoles import ReadPrismRoles
from convert.adapters.freecad.EditShape.Prism.PrismExpected import ExpectedPrism
from convert.adapters.freecad.EditShape.Prism.PrismRaw import PrismRaw, ReadPrismRaw
from convert.adapters.freecad.EditShape.PrismShape import KMaxPrismBytes
from convert.Geometry.Opencascade import (
    BuildModel,
    KIdentityLocation,
    PlacementState,
    PlaceRecordMut,
    Reference,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Payloads.PayloadRecord import BrepPayload


# an occurrence joins an indexed owner to a verified placed topology record
@MakeDataClass(frozen=True, slots=True)
class BoxOccurrence:
    RoleValue: str
    EntityId: str


# the ordinal indexes follow first occurrence in each separate shape family
KBodyRoles = dict[KBoxKind, list[BoxOccurrence]]


# the same native shape record must have one symbolic occurrence path
def ReadBoxOrder(RawValue: PrismRaw) -> tuple[int, ...]:
    Paths: dict[int, tuple[int, ...]] = {}
    Pending: list[tuple[Reference, tuple[int, ...]]] = [(RawValue.RootRef, ())]
    while Pending:
        RefValue, ParentPath = Pending.pop()
        PathValue = ParentPath + ((RefValue.KLocation,) if RefValue.KLocation else ())
        RecordId = RefValue.RecordA
        if RecordId in Paths:
            if Paths[RecordId] != PathValue:
                raise ValueError(
                    "FreeCAD box record has alternate symbolic occurrence paths"
                )
            continue
        Paths[RecordId] = PathValue
        Pending.extend(
            (Child, PathValue)
            for Child in reversed(RawValue.Records[RecordId].Children)
        )
    if Paths.keys() != RawValue.Records.keys():
        raise ValueError("FreeCAD box has unresolved indexed occurrences")
    return tuple(Paths)


# identity placement still allocates the same fresh record ids as the strict reader
def PlaceBoxRecords(
    RawValue: PrismRaw, Prefix: str
) -> tuple[PlacementState, Reference]:
    Locations = tuple(RawValue.Matrix(Value) for Value in RawValue.Chains[1:])
    if not RawValue.RootRef.KLocation or any(
        Value != KIdentityLocation for Value in Locations
    ):
        raise ValueError("FreeCAD box requires its qualified placed identity frame")
    State = PlacementState(
        RawValue.Curves,
        RawValue.Surfaces,
        RawValue.Records,
        Locations,
        Prefix,
        [],
        [],
        {},
        {},
        {},
        {},
    )
    RootIndex = PlaceRecordMut(State, RawValue.RootRef.RecordA, KIdentityLocation)
    if len(State.RecordCache) != len(RawValue.Records):
        raise ValueError("FreeCAD box has ambiguous placed identities")
    return State, Reference(RawValue.RootRef.Orientation, RootIndex)


# the normal strict reader and indexed traversal must agree on the actual body entities
def ReadBoxPrism(
    Payload: BrepPayload,
    BodyId: str,
    ProducerId: str,
    Expected: ExpectedPrism,
) -> tuple[BrepModel, KBodyRoles]:
    DataValue = Payload.data
    if DataValue is None or len(DataValue) > KMaxPrismBytes:
        raise ValueError("FreeCAD box shape payload exceeds the prism proof scope")
    RawValue = ReadPrismRaw(DataValue, 4, True)
    Order = ReadBoxOrder(RawValue)
    Roles = ReadPrismRoles(RawValue, Expected)
    Prefix = "freecad:occ:" + HashBytes(Payload.id.encode("utf-8")).hexdigest()[:20]
    State, RootRef = PlaceBoxRecords(RawValue, Prefix)
    Model = BuildModel(
        tuple(State.PlacedCurves),
        tuple(State.PlacedSurfaces),
        State.PlacedRecords,
        RootRef,
        Prefix,
        BodyId,
        {"brep_payload_id": Payload.id, "feature_id": ProducerId},
    )
    Occurrences: KBodyRoles = {"edge": [], "face": [], "vertex": []}
    for RecordId in Order:
        if RecordId in Roles:
            KindValue, RoleValue = Roles[RecordId]
            Placed = State.RecordCache[RecordId, KIdentityLocation]
            Occurrences[KindValue].append(
                BoxOccurrence(RoleValue, f"{Prefix}:{KindValue}:{Placed}")
            )
    return Model, Occurrences
