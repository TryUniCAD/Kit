from hashlib import sha256 as HashBytes
from math import isfinite as IsFinite

from convert.adapters.freecad.BodyLineage.BoxLineage import (
    BoxElement,
    BoxLineage,
    KBoxKind,
)
from convert.adapters.freecad.BodyLineage.BoxNativeOwner import (
    BoxNativeOwner,
    ReadBoxOwners,
    ReadBoxScalar,
    ReadBoxXmlId,
)
from convert.adapters.freecad.BodyLineage.BoxOccurrences import KBodyRoles, ReadBoxPrism
from convert.adapters.freecad.BodyLineage.BoxShapeOwner import ReadBoxShapes
from convert.adapters.freecad.BodyLineage.CheckBoxMap import CheckBoxMap, KMapKinds
from convert.adapters.freecad.EditShape.CylinderRims import KPositionTolerance
from convert.adapters.freecad.EditShape.Prism.PrismExpected import ExpectedShape
from convert.adapters.freecad.Native import ElemData
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector


# each role is derived from the actual dimensional owner instead of measured shape bounds
def ReadBoxSize(
    Document: CadDocument, OwnerData: BoxNativeOwner, NameValue: str
) -> float:
    Child = OwnerData.ChildObject
    PropValue = Child.properties[NameValue]
    FloatNode = ReadBoxScalar(Child, NameValue, "App::PropertyLength", "Float")
    Drivers = tuple(
        Value
        for Value in Document.parameters
        if Value.attributes.get("freecad_path") == NameValue
    )
    if set(FloatNode.attrib) != {"value"} or len(Drivers) != 1:
        raise ValueError("FreeCAD origin box has an ambiguous dimension property")
    (Driver,) = Drivers
    SizeValue = float(FloatNode.attrib["value"])
    if (
        not IsFinite(SizeValue)
        or SizeValue <= 2.0 * KPositionTolerance
        or Driver.id not in OwnerData.FeatureValue.parameter_ids
        or Driver.owner_id != OwnerData.FeatureValue.id
        or Driver.expression is not None
        or Driver.role is not ParameterRole.KDriving
        or Driver.value.kind is not ValueKind.KLength
        or Driver.value.unit != "mm"
        or type(Driver.value.value) not in (int, float)
        or Driver.value.value != SizeValue
        or Driver.attributes.get("freecad_property") != ElemData(PropValue)
    ):
        raise ValueError(
            "FreeCAD origin box dimension disagrees with its actual primitive owner"
        )
    return SizeValue


# a checked child range still has to name the same physical role on both shapes
def JoinBoxElems(
    BodyRoles: KBodyRoles, ChildRoles: KBodyRoles
) -> tuple[BoxElement, ...]:
    Elements: list[BoxElement] = []
    for KindValue, _, _ in KMapKinds:
        Pairs = zip(BodyRoles[KindValue], ChildRoles[KindValue], strict=True)
        for Ordinal, (BodyItem, ChildItem) in enumerate(Pairs, 1):
            if BodyItem.RoleValue != ChildItem.RoleValue:
                raise ValueError(
                    "FreeCAD ordinal resolves to another actual primitive boundary"
                )
            Elements.append(
                BoxElement(
                    KindValue, Ordinal, Ordinal, BodyItem.EntityId, BodyItem.RoleValue
                )
            )
    return tuple(Elements)


# source planning needs a typed owner while the persisted neutral model remains unchanged
def ReadBoxLineage(Document: CadDocument) -> BoxLineage:
    Document.assert_valid()
    try:
        return BindBoxLineage(Document)
    except (KeyError, TypeError, OverflowError) as ErrorInfo:
        raise ValueError(
            "FreeCAD origin box lineage has a malformed source owner"
        ) from ErrorInfo


# the exported association is rooted in the literal source records and strict body model
def BindBoxLineage(Document: CadDocument) -> BoxLineage:
    Owners = ReadBoxOwners(Document)
    DataValue = ReadBoxShapes(Document, Owners)
    BodyXmlId = ReadBoxXmlId(Owners.BodyObject)
    ChildXmlId = ReadBoxXmlId(Owners.ChildObject)
    Length, Width, Height = (
        ReadBoxSize(Document, Owners, NameValue)
        for NameValue in ("Length", "Width", "Height")
    )
    Profile = (
        PlaneVector(0.0, 0.0),
        PlaneVector(Length, 0.0),
        PlaneVector(Length, Width),
        PlaneVector(0.0, Width),
    )
    Expected = ExpectedShape(KTransformIdentity, Profile, Height)
    Counts: dict[KBoxKind, int] = {
        "edge": len(Expected.Edges),
        "face": len(Expected.Faces),
        "vertex": len(Expected.Points),
    }
    CheckBoxMap(DataValue.MapData, ChildXmlId, Counts)
    BodyId, FeatureId = Owners.BodyValue.id, Owners.FeatureValue.id
    BodyModel, BodyRoles = ReadBoxPrism(
        DataValue.BodyShape, BodyId, FeatureId, Expected
    )
    _, ChildRoles = ReadBoxPrism(DataValue.ChildShape, BodyId, FeatureId, Expected)
    if BodyModel != Document.brep:
        raise ValueError(
            "FreeCAD origin box roles do not target the actual strict B-rep"
        )
    return BoxLineage(
        Document.source.sha256,
        Owners.DocumentUuid,
        BodyXmlId,
        ChildXmlId,
        BodyId,
        FeatureId,
        DataValue.BodyShape.id,
        DataValue.ChildShape.id,
        HashBytes(DataValue.MapData).hexdigest(),
        JoinBoxElems(BodyRoles, ChildRoles),
    )
