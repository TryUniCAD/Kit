from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import (
    LowerBoxModel,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxSource import (
    BoxSource,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckBoxAttach import (
    CheckBoxAttach,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckBoxBody import (
    CheckBoxBody,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxGeometry import (
    ReadBoxGeometry,
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
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxText import (
    ReadBoxText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadTopPlane import (
    ReadTopPlane,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KDimensions,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentModel import CadDocument


# each projected parameter must still reference its actual sketch or feature owner
def ReadBoxBindings(ModelValue: CadDocument) -> dict[str, str]:
    Names = {SketchValue.id: SketchValue.name for SketchValue in ModelValue.sketches}
    Names.update({Feature.id: Feature.name for Feature in ModelValue.feature_timeline})
    return {
        Driver.id: Driver.name + "@" + Names[Driver.owner_id]
        for Driver in ModelValue.parameters
    }


# only source metadata and authored dimensions can select the measured signed lowering
def LowerBoxSource(DocumentValue: CadDocument) -> BoxSource:
    Release = ReadBoxRelease(DocumentValue.source.application_version)
    Feature, Definition, BodyValue, Original = ReadBoxModel(DocumentValue)
    BodyData = NativeRecord(BodyValue.attributes["freecad"])
    FeatureData = Definition.object_data
    PartName = ReadBoxString(FeatureData["name"])
    Objects = ReadBoxObjects(Original, FeatureData, BodyData, Release)
    PlaneValue = ReadTopPlane(DocumentValue.support_planes, Objects)
    Properties = ReadBoxProps(FeatureData, ReadBoxString(BodyData["name"]), Release)
    Flags = (
        CheckBoxBody(
            NativeRecord(BodyData["properties"]), BodyValue.name, PartName, Release
        )
        | ReadBoxOrigin(Objects, Release)
        | CheckBoxAttach(Properties, Feature.name, PlaneValue.id, Release)
    )
    (Length, Width, Height), Sizes = ReadBoxParams(
        DocumentValue.parameters, Feature, Properties, Release
    )
    DriverIds = (Length.id, Width.id, Height.id)
    Geometry = ReadBoxGeometry(DocumentValue, Sizes)
    NameValue, TextValue, Epoch, Units = ReadBoxText(
        DocumentValue.source,
        Original,
        Release,
        BodyValue.name,
        Feature.id,
        DriverIds,
        Flags,
    )
    ModelValue = LowerBoxModel(
        DocumentValue,
        NameValue,
        DriverIds,
        Sizes,
        KDimensions,
        BodyValue.name,
        TopAttached=True,
    )
    return BoxSource(
        ModelValue,
        TextValue,
        Sizes,
        Epoch,
        ReadBoxBindings(ModelValue),
        BodyValue.name,
        Feature.name,
        Geometry,
        Units,
    )


# malformed owners must fail closed before they can enter a native part builder
def ReadBoxSource(DocumentValue: CadDocument) -> BoxSource:
    try:
        return LowerBoxSource(DocumentValue)
    except (KeyError, TypeError, OverflowError) as ErrorInfo:
        raise ValueError(
            "FreeCAD attached box has a malformed source owner"
        ) from ErrorInfo
