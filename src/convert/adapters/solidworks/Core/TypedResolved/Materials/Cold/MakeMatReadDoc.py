from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Materials.PartMatIntent import (
    PartMatIntent,
)
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Materials.PlanMatPart import (
    KMatAnchor,
    KMatCatalog,
    KMatDefaultColor,
)
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckPrismBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import (
    CheckPrismEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Materials.Cold.ReadMatRing import (
    ReadMatRing,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatDensity import (
    ReadMatDensity,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatText import (
    ReadMatText,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.materials.MaterialRecord import MaterialRecord
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


# cold material uses the actual linked positive density and the two token configuration identity
def ReadMatIntent(LinkValue: NativeLink, ConfigValue: ArchiveNode) -> PartMatIntent:
    Visual = RequireNative(ConfigValue.FieldsValue.get("f78"), "moVisualProperties_c")
    Fields = NativeRecord(Visual.FieldsValue.get("f20"))
    CatalogValue, Delimiter, NameValue = ReadMatText(Fields.get("f20")).partition("|")
    if not Delimiter or "|" in NameValue:
        raise ValueError("cold material requires a two token catalog identity")
    return PartMatIntent(
        CatalogValue, NameValue, ReadMatDensity(LinkValue.ConfigValue, ConfigValue)
    )


# file identity and creation time belong to the actual self record and archive header
def ReadMatSelf(LinkValue: NativeLink) -> tuple[str, SelfFileInput]:
    Fields = LinkValue.ConfigValue.HeaderValue.FieldsValue
    FileValue = GetFileRef(Fields.get("f38"))
    EpochValue = Fields.get("f70")
    if type(EpochValue) is not int:
        raise ValueError("cold material lacks the owning part creation time")
    return FileValue.NameValue, RequirePartPath(FileValue.PathValue, EpochValue)


# the finite shape must follow the actual principal plane referenced by the retained profile
def ReadMatPlane(
    Owner: ExtrudeOwner, LinkValue: NativeLink, Features: Mapping[int, ArchiveNode]
) -> SupportPlane:
    FrameValue = ReadPrismFrame(
        Owner.ProfileValue, LinkValue.ConfigValue.RootValue, Features
    )
    RefValue = RequireNative(
        Owner.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    Identity = NativeRecord(RefValue.FieldsValue.get("ff0")).get("f00")
    if type(Identity) is not int or Identity not in Features:
        raise ValueError("cold material sketch lacks its actual support owner")
    return SupportPlane(
        f"sldprt:plane:{Identity}", ReadNativeName(Features[Identity]), FrameValue
    )


# the body creator and its sole positive blind depth come from the retained native feature
def MakeMatBoss(Owner: ExtrudeOwner, SketchId: str) -> tuple[FeatureStep, Parameter]:
    Depth = Owner.RequireDepth()
    FeatureId = f"sldprt:feature:{NativeNodeId(Owner.NodeValue)}"
    Value = ParameterValue(
        RequireScalar(Depth.Parameter.FieldsValue.get("f58")), ValueKind.KLength, "m"
    )
    Drive = Parameter(
        f"{FeatureId}/depth",
        Depth.DepthValue.name,
        Value,
        ParameterRole.KDriving,
        owner_id=FeatureId,
    )
    return (
        FeatureStep(
            FeatureId,
            ReadNativeName(Owner.NodeValue),
            FeatureKind.KExtrusion,
            0,
            sketch_id=SketchId,
            parameter_ids=(Drive.id,),
            operation=BooleanOp.KCreate,
            definition=ExtrudeFeature(Value, ExtrudeEnd.KBlind, False, False),
        ),
        Drive,
    )


# actual archive owners yield one canonical editable material model and its own save locator
def MakeMatReadDoc(
    LinkValue: NativeLink, ConfigValue: ArchiveNode
) -> tuple[CadDocument, SelfFileInput]:
    Features = IndexFeatures(LinkValue)
    (BossValue,) = (
        Value
        for Value in Features.values()
        if Value.ClassValue.NameValue == "moExtrusion_c"
    )
    Owner = ReadExtrude(LinkValue, BossValue, Features)
    CheckPrismBoss(Owner, AllowFirstScope=True)
    CheckPrismEnd(Owner)
    PlaneValue = ReadMatPlane(Owner, LinkValue, Features)
    SketchValue, Drivers, KindValue = ReadMatRing(
        Owner.ProfileValue, LinkValue, PlaneValue.id
    )
    FeatureValue, Depth = MakeMatBoss(Owner, SketchValue.id)
    NameValue, FileValue = ReadMatSelf(LinkValue)
    IntentValue = ReadMatIntent(LinkValue, ConfigValue)
    MaterialValue = MaterialRecord(
        f"{FeatureValue.id}/material",
        IntentValue.NameValue,
        IntentValue.DensityValue,
        KMatDefaultColor,
    )
    BodyValue = DesignBody(
        f"{FeatureValue.id}/body",
        FeatureValue.name,
        FeatureValue.id,
        material_id=MaterialValue.id,
    )
    Config = Configuration("sldprt:configuration:0", ReadNativeName(ConfigValue), True)
    return CadDocument(
        CadSource("kit-neutral", "", ""),
        (Config,),
        (*Drivers, Depth),
        (PlaneValue,),
        (SketchValue,),
        (),
        (FeatureValue,),
        (BodyValue,),
        materials=(MaterialValue,),
        metadata={
            "name": NameValue,
            KMatAnchor: KindValue,
            KMatCatalog: IntentValue.CatalogValue,
        },
    ), FileValue
