from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Patterns.BindPatBody import (
    BindPatBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.BindPatStep import (
    BindPatStep,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.MakePatParam import (
    MakePatParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.MakePatSelect import (
    MakePatSelect,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import NativeFeature


# the typed pattern applies only to its authenticated saved or independently computed body
def ApplyPatDoc(
    Document: CadDocument,
    LinkValue: NativeLink,
    OwnerValue: PatternOwner,
    Surface: StockCacheBody | None,
) -> CadDocument:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    FeatureId = f"sldprt:feature:{NativeId}"
    SeedKey = f"sldprt:feature:{NativeNodeId(OwnerValue.SeedValue)}"
    PlaneKey = f"sldprt:feature:{NativeNodeId(OwnerValue.DatumValue.PlaneValue)}"
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    StepValue, SeedValue = Steps[FeatureId], Steps[SeedKey]
    Params = tuple(
        Value for Value in Document.parameters if Value.owner_id == FeatureId
    )
    if (
        StepValue.kind != FeatureKind.KPattern
        or StepValue.operation != "linear_pattern"
        or not isinstance(StepValue.definition, NativeFeature)
        or StepValue.name != ReadNativeName(OwnerValue.NodeValue)
        or StepValue.suppressed
        or StepValue.configuration_states
        or StepValue.sketch_id is not None
        or not isinstance(SeedValue.definition, ExtrudeFeature)
        or SeedValue.suppressed
        or SeedValue.configuration_states
        or SeedValue.name != ReadNativeName(OwnerValue.SeedValue)
        or Steps[PlaneKey].order >= StepValue.order
        or tuple(Value.id for Value in Params) != StepValue.parameter_ids
        or len(Params) != 2
    ):
        raise ValueError(
            "pattern lacks its actual neutral step and owned seed and parameters"
        )
    ParamMap = {Value.id: Value for Value in Params}
    Count, Pitch = (
        MakePatParam(
            ParamMap[f"sldprt:parameter:{NativeId}:{Driver.NativeName}"],
            Driver,
            LinkValue,
        )
        for Driver in OwnerValue.DriversValue[:2]
    )
    SelectValue = MakePatSelect(Document, LinkValue, OwnerValue)
    BoundStep = BindPatStep(StepValue, OwnerValue, LinkValue, SelectValue, Count, Pitch)
    if any(
        Value.id == SelectValue.id
        or set(Value.selection_ids).intersection(StepValue.selection_ids)
        for Value in Document.feature_timeline
        if Value is not StepValue
    ) or any(Value.id == SelectValue.id for Value in Document.selections):
        raise ValueError(
            "pattern selection conflicts with another existing neutral owner"
        )
    ModelValue = Document.brep
    (BodyValue,) = Document.bodies
    if ModelValue is None or BodyValue.final_feature_id != StepValue.id:
        raise ValueError("pattern final public body identity differs")
    Parameters = {Count.id: Count, Pitch.id: Pitch}
    Evidence = {
        "status": (
            "projected_saved_single_direction"
            if Surface is not None
            else "projected_cold_single_direction"
        ),
        "native_atom_lineage": OwnerValue.AtomsValue,
        "physical_body_node": (
            Surface.KernelValue.IndexValue if Surface is not None else None
        ),
        "driver_roles": tuple(
            (Driver.NativeName, Driver.LiveValue, Driver.CacheValue)
            for Driver in OwnerValue.DriversValue
        ),
        "public_writer_qualified": False,
    }
    if Surface is None:
        BrepValue = ModelValue
        BoundBody = ReplaceValue(
            BodyValue,
            attributes=FreezeMapping(
                {**BodyValue.attributes, "solidworks.native_body": Evidence}
            ),
        )
    else:
        BrepValue, BoundBody = BindPatBody(
            ModelValue, BodyValue, Surface.NameValue, Evidence
        )
    return ReplaceValue(
        Document,
        brep=BrepValue,
        bodies=(BoundBody,),
        parameters=tuple(
            Parameters.get(Value.id, Value) for Value in Document.parameters
        ),
        selections=tuple(
            Value
            for Value in Document.selections
            if Value.id not in StepValue.selection_ids
        )
        + (SelectValue,),
        feature_timeline=tuple(
            BoundStep if Value is StepValue else Value
            for Value in Document.feature_timeline
        ),
        metadata=FreezeMapping(
            {**Document.metadata, "solidworks.typed_linear_pattern": Evidence}
        ),
    )
