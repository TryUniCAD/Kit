from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDef import (
    ReadChmfDef,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    EdgeChmfRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.BindPrismCreate import (
    BindPrismCreate,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Selection import Selection, SelectPathElem


# both live values retain their actual parameter nodes and neutral owner identities
def BindChmfParam(
    ParamValue: Parameter,
    Driver: ChmfDriver,
    LinkValue: NativeLink,
    Angular: bool,
) -> Parameter:
    if ParamValue.name != Driver.NameValue or ParamValue.expression is not None:
        raise ValueError(
            "cold chamfer native and neutral driving parameter roles disagree"
        )
    Value = (
        ParameterValue(Driver.ValueSi, ValueKind.KAngle, "rad")
        if Angular
        else ParameterValue(Driver.ValueSi * 1000, ValueKind.KLength, "mm")
    )
    Provenance = TypedProvenance(
        NativeNodeSpan(LinkValue, Driver.ParameterNode), ParamValue.id
    )
    if Provenance is None:
        raise ValueError("chamfer live parameter lacks its actual typed archive span")
    return ReplaceValue(
        ParamValue,
        value=Value,
        role=ParameterRole.KDriving,
        provenance=Provenance,
        attributes=FreezeMapping(
            {
                **ParamValue.attributes,
                "typed_dimension_owner": NativeNodeSpan(
                    LinkValue, Driver.DimensionNode
                ),
                "typed_display_owner": NativeNodeSpan(LinkValue, Driver.DisplayNode),
                "persistent_dimension_id": Driver.DimensionNode.FieldsValue["f50"],
            }
        ),
    )


# the selected edge and first incident face have separate portable witnesses and archive owners
def MakeChmfPicks(
    PartValue: ChmfPartRead,
    BossValue: FeatureStep,
    StepValue: FeatureStep,
) -> tuple[Selection, Selection]:
    OwnerValue, EdgeValue = PartValue.OwnersValue, PartValue.EdgeValue
    LinkValue = PartValue.LinkValue
    EdgeNode = OwnerValue.SelectedRef
    FaceNode = EdgeChmfRows(EdgeNode)[0]
    EdgeId, FaceId = StepValue.id + ":edge", StepValue.id + ":distance-face"
    return (
        Selection(
            EdgeId,
            BossValue.name + " edge",
            (SelectPathElem("feature", BossValue.id, "edge"),),
            point=EdgeValue.EdgePoint,
            provenance=TypedProvenance(NativeNodeSpan(LinkValue, EdgeNode), EdgeId),
        ),
        Selection(
            FaceId,
            BossValue.name + " distance face",
            (SelectPathElem("feature", BossValue.id, "distance face"),),
            point=EdgeValue.FacePoint,
            provenance=TypedProvenance(NativeNodeSpan(LinkValue, FaceNode), FaceId),
        ),
    )


# the portable operation must reuse the actual step and its original predecessor dependencies
def ReadChmfSteps(
    Document: CadDocument,
    PartValue: ChmfPartRead,
) -> tuple[FeatureStep, FeatureStep]:
    Owners = PartValue.OwnersValue
    StockId = f"sldprt:feature:{NativeNodeId(Owners.StockValue)}"
    FeatureId = f"sldprt:feature:{NativeNodeId(Owners.FeatureValue)}"
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    StockValue, StepValue = Steps[StockId], Steps[FeatureId]
    if (
        StockValue.order >= StepValue.order
        or StepValue.kind != FeatureKind.KChamfer
        or not isinstance(StepValue.definition, NativeFeature)
        or StepValue.operation is not None
        or StepValue.sketch_id is not None
        or StepValue.selection_ids
        or StepValue.suppressed
        or StepValue.configuration_states
        or StepValue.input_feature_ids != (StockId,)
        or StepValue.name != ReadNativeName(Owners.FeatureValue)
        or not isinstance(StockValue.definition, ExtrudeFeature)
    ):
        raise ValueError(
            "cold chamfer lacks its original public stock or operation identity"
        )
    return StockValue, StepValue


# the portable history joins the actual active drives and both selected roles to their original feature
def BindChmfDoc(Document: CadDocument, PartValue: ChmfPartRead) -> CadDocument:
    StockValue, StepValue = ReadChmfSteps(Document, PartValue)
    Owners, LinkValue = PartValue.OwnersValue, PartValue.LinkValue
    (BodyValue,) = Document.bodies
    Params = tuple(
        Value for Value in Document.parameters if Value.owner_id == StepValue.id
    )
    Drivers = Owners.DriversValue
    if (
        BodyValue.final_feature_id != StepValue.id
        or len(Params) != len(Drivers)
        or tuple(Value.id for Value in Params) != StepValue.parameter_ids
    ):
        raise ValueError(
            "cold chamfer does not own the actual neutral result body and independent drivers"
        )
    Bound = tuple(
        BindChmfParam(Param, Driver, LinkValue, Driver is Owners.AngleValue)
        for Param, Driver in zip(Params, Drivers, strict=True)
    )
    Picks = MakeChmfPicks(PartValue, StockValue, StepValue)
    IdsValue = tuple(Value.id for Value in Picks)
    if set(IdsValue).intersection(Value.id for Value in Document.selections):
        raise ValueError("chamfer selections repeat an existing neutral owner")
    Definition = ReadChmfDef(Owners.ModeWord, Bound)
    Updated = {
        StepValue.id: ReplaceValue(
            StepValue, definition=Definition, selection_ids=IdsValue
        ),
    }
    SavedValue = PartValue.WarmValue is not None
    if not SavedValue:
        Updated[StockValue.id] = ReplaceValue(StockValue, operation=BooleanOp.KCreate)
    ParamValues = {Value.id: Value for Value in Bound}
    Projected = ReplaceValue(
        Document,
        parameters=tuple(
            ParamValues.get(Value.id, Value) for Value in Document.parameters
        ),
        selections=(*Document.selections, *Picks),
        feature_timeline=tuple(
            Updated.get(Value.id, Value) for Value in Document.feature_timeline
        ),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=StepValue.name if SavedValue else StockValue.name,
                provenance=(
                    StepValue.provenance if SavedValue else StockValue.provenance
                ),
                attributes=(
                    FreezeMapping(
                        {
                            **BodyValue.attributes,
                            "native_object_id": NativeNodeId(Owners.FeatureValue),
                        }
                    )
                    if SavedValue
                    else BodyValue.attributes
                ),
            ),
        ),
    )
    return (
        BindPrismCreate(Projected, StockValue, FirstScope=True)
        if SavedValue
        else Projected
    )
