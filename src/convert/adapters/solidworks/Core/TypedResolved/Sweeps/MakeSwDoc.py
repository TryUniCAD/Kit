from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwBody import MakeSwBody
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwSketch import (
    MakeSwSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwResult import (
    SwSavedBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwState import (
    SwReadState,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.SweepFeature import SweepFeature
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


# standard datum planes preserve actual orthonormal tangent axes from typed native records
def MakeSwDatum(StateValue: SwReadGraph, DatumValue: ArchiveNode) -> SupportPlane:
    FrameValue, _ = ReadDatumFrame(DatumValue)
    NativeId = NativeNodeId(DatumValue)
    TransformValue = Transform(
        SpaceVector(*(Value * 1000.0 for Value in FrameValue.OriginValue)),
        SpaceVector(*FrameValue.AxisU),
        SpaceVector(*FrameValue.AxisV),
        SpaceVector(*FrameValue.NormalValue),
    )
    return SupportPlane(
        f"sldprt:plane:{NativeId}",
        ReadNativeName(DatumValue),
        TransformValue,
        provenance=TypedProvenance(
            NativeNodeSpan(StateValue.LinkValue, DatumValue), str(NativeId)
        ),
    )


# cold publication still compares the same strict projection it generated before any saved read support
def MakeSwDoc(
    StateValue: SwReadState, SourceValue: CadSource, IncludeBrep: bool
) -> CadDocument:
    return MakeSwDesign(
        StateValue, SourceValue, StateValue.IntentValue.NameValue, IncludeBrep
    )


# portable history retains the ordered profile owners independent of result framing
def MakeSwDesign(
    StateValue: SwReadGraph,
    SourceValue: CadSource,
    NameValue: str,
    IncludeBrep: bool,
    SavedBody: SwSavedBody | None = None,
) -> CadDocument:
    LinkValue = StateValue.LinkValue
    SectionValue, Diameter = MakeSwSketch(LinkValue, StateValue.SectionValue)
    PathValue, Radius = MakeSwSketch(LinkValue, StateValue.PathValue)
    FeatureOwner = StateValue.FeatureValue
    NativeId = NativeNodeId(FeatureOwner)
    FeatureValue = FeatureStep(
        f"sldprt:feature:{NativeId}",
        ReadNativeName(FeatureOwner),
        FeatureKind.KSweep,
        1,
        sketch_id=SectionValue.id,
        operation=BooleanOp.KCreate,
        definition=SweepFeature(PathValue.id),
        provenance=TypedProvenance(
            NativeNodeSpan(LinkValue, FeatureOwner), str(NativeId)
        ),
    )
    BodyValue, BrepValue = MakeSwBody(StateValue, FeatureValue, IncludeBrep, SavedBody)
    DensityValue = Parameter(
        f"{BodyValue.id}:density",
        "Density",
        ParameterValue(
            RequireScalar(StateValue.DensityValue.FieldsValue.get("f58")),
            ValueKind.KQuantity,
            "kg/m3",
        ),
        owner_id=BodyValue.id,
        provenance=TypedProvenance(
            NativeNodeSpan(LinkValue, StateValue.DensityValue), ""
        ),
    )
    ConfigValue = StateValue.ConfigValue
    DocValue = CadDocument(
        SourceValue,
        (
            Configuration(
                f"sldprt:configuration:{NativeNodeId(ConfigValue)}",
                ReadNativeName(ConfigValue),
                True,
                attributes=(
                    {"native_configuration_id": NativeNodeId(ConfigValue)}
                    if SavedBody is not None
                    else {}
                ),
            ),
        ),
        (Diameter, Radius, DensityValue),
        tuple(MakeSwDatum(StateValue, Value) for Value in StateValue.DatumValues),
        (SectionValue, PathValue),
        (),
        (FeatureValue,),
        (BodyValue,),
        metadata={"name": NameValue},
        brep=BrepValue,
    )
    return ReplaceValue(DocValue, capabilities=InferCaps(DocValue))
