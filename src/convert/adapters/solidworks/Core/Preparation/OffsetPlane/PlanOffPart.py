from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import (
    ProjectCircle,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ReadOffIntent import (
    ReadOffIntent,
)
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import RefPlaneFeature


# the supported portable offset owns its sole circular sketch before delegating the ordinary blind boss checks
def PlanOffPart(DocumentValue: CadDocument) -> tuple[CirclePlan, OffsetInput]:
    CheckPlainScope(DocumentValue)
    DocumentValue.assert_valid()
    if (
        DocumentValue.units != "mm"
        or not DocumentValue.capabilities <= KPartWriteCaps
        or len(DocumentValue.support_planes) != 2
    ):
        raise ValueError("offset plane part requires its two modeled supports")
    OffsetStep, BossStep = DocumentValue.feature_timeline
    (SketchValue,) = DocumentValue.sketches
    Definition = OffsetStep.definition
    if (
        type(Definition) is not RefPlaneFeature
        or OffsetStep.order >= BossStep.order
        or len(OffsetStep.parameter_ids) != 1
        or Definition.reference_plane_id == Definition.support_plane_id
        or BossStep.input_feature_ids != (OffsetStep.id,)
        or SketchValue.support_plane_id != Definition.support_plane_id
        or any(
            RuleValue.provenance is not None for RuleValue in SketchValue.constraints
        )
    ):
        raise ValueError("offset plane part requires its ordered datum sketch and boss")
    PlanesValue = {
        PlaneValue.id: PlaneValue for PlaneValue in DocumentValue.support_planes
    }
    Parameters = {Param.id: Param for Param in DocumentValue.parameters}
    BaseValue = PlanesValue.get(Definition.reference_plane_id)
    CarrierValue = PlanesValue.get(Definition.support_plane_id)
    Driver = Parameters.get(OffsetStep.parameter_ids[0])
    if BaseValue is None or CarrierValue is None or Driver is None:
        raise ValueError("offset plane has a dangling support or driving parameter")
    DatumValue = ReadOffIntent(OffsetStep, BaseValue, CarrierValue, Driver)
    PlanValue = ProjectCircle(
        ReplaceValue(
            DocumentValue,
            support_planes=(BaseValue,),
            sketches=(ReplaceValue(SketchValue, support_plane_id=BaseValue.id),),
            feature_timeline=(ReplaceValue(BossStep, input_feature_ids=()),),
            parameters=tuple(
                Param for Param in DocumentValue.parameters if Param is not Driver
            ),
        )
    )
    if (
        PlanValue.IsDiameter
        or PlanValue.CircleValue.CenterValue != (0.0, 0.0)
        or PlanValue.EndValue.IsReversed
        or PlanValue.EndValue.ModeValue != "blind"
    ):
        raise ValueError("offset plane requires one centered fixed radius circle")
    return PlanValue, DatumValue
