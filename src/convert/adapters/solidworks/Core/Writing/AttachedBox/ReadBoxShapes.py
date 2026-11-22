from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.freecad.BodyLineage.BoxPrismRoles import ReadPrismRoles
from convert.adapters.freecad.EditShape.Prism.PrismExpected import (
    ExpectedPrism,
    ExpectedShape,
)
from convert.adapters.freecad.EditShape.Prism.PrismRaw import ReadPrismRaw
from convert.adapters.freecad.EditShape.PrismShape import KMaxPrismBytes
from convert.adapters.freecad.Native import NativeArchive
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxSource import (
    BoxSource,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxShapeFields import (
    BoxShapeFields,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import NativeFeature
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector

# each legacy shape property has a known owning coordinate role
KShapeFields = (("body", "Shape"), ("feature", "AddSubShape"), ("feature", "Shape"))


# boundary roles derive from actual editable box dimensions and its rigid source support
def BoxShapeModel(SourceValue: BoxSource, IsLocal: bool) -> ExpectedPrism:
    Length, Width, Height = SourceValue.DimensionsValue
    Width = Width if IsLocal else -Width
    Profile = (
        PlaneVector(0.0, 0.0),
        PlaneVector(Length, 0.0),
        PlaneVector(Length, Width),
        PlaneVector(0.0, Width),
    )
    Frame = (
        KTransformIdentity
        if IsLocal
        else SourceValue.ModelValue.support_planes[0].transform
    )
    return ExpectedShape(Frame, Profile, Height if IsLocal else -Height)


# inspect all three physical cache boundaries before describing them as source evidence
def ReadBoxShapes(
    DocumentValue: CadDocument, ArchiveValue: NativeArchive, SourceValue: BoxSource
) -> tuple[dict[str, object], ...]:
    BodyValue, Feature = DocumentValue.bodies[0], DocumentValue.feature_timeline[0]
    Definition = Feature.definition
    if not isinstance(Definition, NativeFeature):
        raise ValueError("attached shape proof requires its actual source primitive")
    ObjectNames = {
        "body": NativeRecord(BodyValue.attributes["freecad"])["name"],
        "feature": Definition.object_data["name"],
    }
    Objects = {Value.name: Value for Value in ArchiveValue.objects}
    Payloads = {Value.id: Value for Value in DocumentValue.brep_payloads}
    Results: list[dict[str, object]] = []
    for EntityName, PropertyName in KShapeFields:
        NameValue = ObjectNames[EntityName]
        if not isinstance(NameValue, str):
            raise ValueError("FreeCAD attached shape has no actual source object")
        Payload = Payloads[f"freecad:brep:{NameValue}:{PropertyName}"]
        OwnerValue = BodyValue if EntityName == "body" else Feature
        Links = OwnerValue.attributes["brep_payload_ids"]
        if not isinstance(Links, (list, tuple)) or Payload.id not in CastValue(
            Sequence[object], Links
        ):
            raise ValueError("FreeCAD attached shape has a different neutral owner")
        SourceBytes = BoxShapeFields(
            ArchiveValue, Objects[NameValue], PropertyName, Payload
        )
        IsLocal = PropertyName == "AddSubShape"
        if len(SourceBytes) > KMaxPrismBytes:
            raise ValueError(
                "FreeCAD attached box shape exceeds its checked prism scope"
            )
        Expected = BoxShapeModel(SourceValue, IsLocal)
        RolesValue = ReadPrismRoles(ReadPrismRaw(SourceBytes, 4, True), Expected)
        Results.append(
            {
                "id": Payload.id,
                "owner": OwnerValue.id,
                "property": PropertyName,
                "member": Payload.source_stream,
                "sha256": Payload.sha256,
                "coordinate_frame": "feature" if IsLocal else "model",
                "physical_roles": [
                    {"kind": KindValue, "role": RoleValue}
                    for KindValue, RoleValue in sorted(RolesValue.values())
                ],
            }
        )
    if len({Value["member"] for Value in Results}) != len(Results) or set(
        ArchiveValue.entries
    ) != {str(Value["member"]) for Value in Results}:
        raise ValueError("FreeCAD attached box has other source archive members")
    return tuple(Results)
