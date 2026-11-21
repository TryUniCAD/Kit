from convert.adapters.freecad.BodyLineage.BoxLineage import KBoxKind
from convert.adapters.freecad.EditShape.Prism.PrismExpected import ExpectedPrism
from convert.adapters.freecad.EditShape.Prism.PrismFaces import CheckFaceMut
from convert.adapters.freecad.EditShape.Prism.PrismProof import PrismProof
from convert.adapters.freecad.EditShape.Prism.PrismRaw import PrismRaw
from convert.adapters.freecad.EditShape.PrismShape import HasUsedCarriers

# proof results connect original records to dimension derived boundary roles
KRecordRoles = dict[int, tuple[KBoxKind, str]]


# signed corner and boundary roles are independent of storage and traversal order
def FindBoxRole(Expected: ExpectedPrism, Indices: tuple[int, ...]) -> str:
    Points = tuple(Expected.Points[Index] for Index in Indices)
    Columns = zip(*((Point.x, Point.y, Point.z) for Point in Points), strict=True)
    return "".join(
        "*" if min(Column) != max(Column) else "0" if Column[0] == 0.0 else "1"
        for Column in Columns
    )


# one complete physical prism proof supplies the actual face edge and vertex keys
def ReadPrismRoles(RawValue: PrismRaw, Expected: ExpectedPrism) -> KRecordRoles:
    Proof = PrismProof(RawValue, Expected)
    RootPlace = RawValue.Place(RawValue.RootRef)
    (ShellRef,) = RawValue.Records[RawValue.RootRef.RecordA].Children
    ShellPlace = RawValue.Place(ShellRef, RootPlace)
    FaceRefs = RawValue.Records[ShellRef.RecordA].Children
    Faces = {
        RefValue.RecordA: CheckFaceMut(Proof, ShellRef, RefValue, ShellPlace)
        for RefValue in FaceRefs
    }
    if (
        len(Faces) != len(FaceRefs)
        or set(Faces.values()) != Expected.Faces.keys()
        or len(Proof.Vertices) != len(Expected.Points)
        or len(Proof.Edges) != len(Expected.Edges)
        or not HasUsedCarriers(Proof)
    ):
        raise ValueError(
            "FreeCAD origin box shape has incomplete physical boundary roles"
        )
    Roles: KRecordRoles = {
        Index: ("face", FindBoxRole(Expected, Value)) for Index, Value in Faces.items()
    }
    Roles.update(
        {
            Index: ("edge", FindBoxRole(Expected, Value))
            for (Index, _), Value in Proof.Edges.items()
        }
    )
    Roles.update(
        {
            Index: ("vertex", FindBoxRole(Expected, (Value,)))
            for (Index, _), Value in Proof.Vertices.items()
        }
    )
    if len(Roles) != len(Faces) + len(Proof.Edges) + len(Proof.Vertices) or len(
        set(Roles.values())
    ) != len(Roles):
        raise ValueError(
            "FreeCAD origin box shape has ambiguous physical boundary roles"
        )
    return Roles
