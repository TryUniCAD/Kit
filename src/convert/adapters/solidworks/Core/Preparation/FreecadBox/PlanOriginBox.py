from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.BodyLineage.BoxLineage import BoxLineage
from convert.adapters.freecad.BodyLineage.ReadBoxLineage import ReadBoxLineage
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import (
    LowerBoxModel,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxDatums import (
    BoxDatums,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxSource import (
    BoxSource,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckBoxAttach import (
    ReadBoxFlags,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckBoxBody import (
    CheckBoxBody,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckIdentity import (
    CheckIdentity,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxGeometry import (
    ReadBoxGeometry,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxDatums import (
    ReadBoxDatums,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxModel import (
    ReadBoxModel,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxObjects import (
    ReadBoxObjects,
    ReadBoxProps,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxOrigin import (
    ReadBoxOrigin,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxParams import (
    ReadBoxParams,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxRelease import (
    ReadBoxRelease,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import (
    ReadBoxBindings,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxText import (
    ReadBoxText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadTopPlane import (
    ReadBoxPlane,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    RequireEmpty,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KDimensions,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.Records.RecordParameter import Parameter


# the original source owners must remain explicit beside the target construction intent
@MakeDataClass(frozen=True, slots=True)
class OriginBoxPlan:
    SourceDocument: CadDocument
    SourceLineage: BoxLineage
    SourcePlane: SupportPlane
    SourcePlacement: Transform
    SourceDrivers: tuple[Parameter, Parameter, Parameter]
    PartSource: BoxSource
    SourceDatums: BoxDatums


# ordinary primitive geometry is rooted in its local frame without an attachment
def ReadOriginFlags(
    Properties: Mapping[str, object], NameValue: str, Release: str
) -> dict[str, str]:
    CheckIdentity(Properties, "Placement")
    CheckIdentity(Properties, "AttachmentOffset")
    RequireEmpty(Properties, "AttachmentSupport", "LinkSubList", "LinkSubList")
    return ReadBoxFlags(Properties, NameValue, "0", Release)


# the construction model keeps live parameters while the full source stays in the plan
def BuildOriginPart(
    Document: CadDocument,
    Metadata: Mapping[str, object],
    Release: str,
    Drivers: tuple[Parameter, Parameter, Parameter],
    Sizes: tuple[float, float, float],
    Flags: Mapping[str, str],
) -> BoxSource:
    (BodyValue,) = Document.bodies
    (FeatureValue,) = Document.feature_timeline
    Length, Width, Height = Drivers
    DriverIds = (Length.id, Width.id, Height.id)
    NameValue, TextValue, Epoch, Units = ReadBoxText(
        Document.source,
        Metadata,
        Release,
        BodyValue.name,
        FeatureValue.id,
        DriverIds,
        Flags,
    )
    Model = LowerBoxModel(
        Document, NameValue, DriverIds, Sizes, KDimensions, BodyValue.name
    )
    return BoxSource(
        Model,
        TextValue,
        Sizes,
        Epoch,
        ReadBoxBindings(Model),
        BodyValue.name,
        FeatureValue.name,
        ReadBoxGeometry(Document, Sizes, TopAttached=False),
        Units,
    )


# origin planning requires both strict source ownership and the sourced identity frame
def ReadOriginPlan(Document: CadDocument) -> OriginBoxPlan:
    Lineage = ReadBoxLineage(Document)
    Release = ReadBoxRelease(Document.source.application_version)
    Feature, Definition, BodyValue, Metadata = ReadBoxModel(Document)
    BodyData = NativeRecord(BodyValue.attributes["freecad"])
    FeatureData = Definition.object_data
    BodyName = ReadBoxString(BodyData["name"])
    PartName = ReadBoxString(FeatureData["name"])
    Objects = ReadBoxObjects(Metadata, FeatureData, BodyData, Release)
    PlaneValue = ReadBoxPlane(Document.support_planes, Objects, "XY-plane")
    Properties = ReadBoxProps(FeatureData, BodyName, Release, TopAttached=False)
    Flags = (
        CheckBoxBody(
            NativeRecord(BodyData["properties"]), BodyValue.name, PartName, Release
        )
        | ReadBoxOrigin(Objects, Release)
        | ReadOriginFlags(Properties, Feature.name, Release)
    )
    Drivers, Sizes = ReadBoxParams(Document.parameters, Feature, Properties, Release)
    PartValue = BuildOriginPart(Document, Metadata, Release, Drivers, Sizes, Flags)
    RequireBox(
        PartValue.PropertiesValue.DocumentFields["FreeCAD Uid"] == Lineage.DocumentUuid,
        "FreeCAD projected properties disagree with the original document identity",
    )
    return OriginBoxPlan(
        Document,
        Lineage,
        PlaneValue,
        PlaneValue.transform,
        Drivers,
        PartValue,
        ReadBoxDatums(Document),
    )


# incomplete source metadata must refuse before any target construction is attempted
def PlanOriginBox(Document: CadDocument) -> OriginBoxPlan:
    try:
        return ReadOriginPlan(Document)
    except (KeyError, TypeError, OverflowError) as ErrorInfo:
        raise ValueError(
            "FreeCAD origin box has a malformed planning owner"
        ) from ErrorInfo
