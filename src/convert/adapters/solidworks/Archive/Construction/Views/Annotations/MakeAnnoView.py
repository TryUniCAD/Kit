from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
    KAnnoBasis,
)
from convert.adapters.solidworks.Archive.Construction.Views.MakeViewNode import (
    MakeViewNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the world aligned view retains the independent identity constructor transform
KAnnoWorld: KAnnoBasis = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


# view frames are independently supplied rotations drawn from the signed principal model axes
def ReadAnnoBasis(Value: object) -> KAnnoBasis:
    if not isinstance(Value, (tuple, list)):
        raise ValueError("annotation frame requires three explicit signed model axes")
    AxesValue = CastValue(Sequence[object], Value)
    if len(AxesValue) != 3 or any(
        not isinstance(AxisValue, (tuple, list))
        or len(CastValue(Sequence[object], AxisValue)) != 3
        for AxisValue in AxesValue
    ):
        raise ValueError("annotation frame requires three explicit signed model axes")
    Basis = CastValue(
        KAnnoBasis,
        tuple(tuple(CastValue(Sequence[object], AxisValue)) for AxisValue in AxesValue),
    )
    if (
        any(
            type(Entry) is not float or Entry not in (-1.0, 0.0, 1.0)
            for AxisValue in Basis
            for Entry in AxisValue
        )
        or any(sum(Entry * Entry for Entry in AxisValue) != 1.0 for AxisValue in Basis)
        or CrossVector(Basis[0], Basis[1]) != Basis[2]
    ):
        raise ValueError("annotation frame requires a right-handed model-axis rotation")
    return Basis


# a rotated annotation uses explicit matrix entries in the native column order
def MakeAnnoFrame(Value: KAnnoBasis) -> dict[str, object]:
    Basis = ReadAnnoBasis(Value)
    Transform = IdentityXform()
    if Basis != KAnnoWorld:
        Transform.update(
            has_matrix=1,
            f08={
                f"m{3 * RowIndex + Column}": Basis[Column][RowIndex]
                for RowIndex in range(3)
                for Column in range(3)
            },
        )
    return Transform


# annotation views extend the existing view initializer with the ownerless subtype state
def MakeAnnoView(InputValue: AnnoViewInput, ViewId: int) -> ArchiveNode:
    NameValue = InputValue.NameValue
    if type(NameValue) is not str or not NameValue or "\x00" in NameValue:
        raise ValueError("annotation view needs an explicit authored name")
    Fields = MakeViewNode(NameValue, ViewId, None).FieldsValue
    Fields.update(
        f368=MakeAnnoFrame(InputValue.BasisValue),
        f3d8=0,
        f3d0=None,
        f3f0=0,
        f3e0=0.0,
        f3e8=None,
        f3f4=0,
        f3f8=1,
        f2f0=None,
        f3fc=-1,
        f408=0,
        f400=-1,
        f404=-1,
    )
    return ArchiveNode(RuntimeClass("moAnnotationView_c", 1), Fields)
