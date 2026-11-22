from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.CheckSelectedRevolveBands import (
    CheckCutBands,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.ReadSelectedStock import (
    ReadStockIndex,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.SelectedRevolvePlan import (
    SelectedRevPlan,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch


# each stock and the cut reuse the signed ordinary profile rules with only their own neutral owners
def ProjectRevOp(
    DocumentValue: CadDocument, Feature: FeatureStep, SketchValue: Sketch
) -> RevolvePlan:
    Definition = Feature.definition
    if (
        type(Definition) is not AngularRevolve
        or Feature.provenance is not None
        or SketchValue.provenance is not None
        or any(Entity.provenance is not None for Entity in SketchValue.entities)
        or any(Relation.provenance is not None for Relation in SketchValue.constraints)
    ):
        raise ValueError("selected revolve operation has an unsupported source owner")
    Params = {Value.id: Value for Value in DocumentValue.parameters}
    Picks = {Value.id: Value for Value in DocumentValue.selections}
    Parameter = Params.get(Definition.AlongParameterId)
    AxisPick = Picks.get(Definition.AxisSelectionId)
    if (
        Parameter is None
        or AxisPick is None
        or Definition.SideMode != "one_sided"
        or Feature.parameter_ids != (Parameter.id,)
        or Feature.selection_ids[:1] != (AxisPick.id,)
        or len(Feature.selection_ids)
        != (2 if Feature.operation is BooleanOp.KCutOperation else 1)
        or AxisPick.name != "Selected local construction axis"
        or AxisPick.provenance is not None
        or Parameter.provenance is not None
    ):
        raise ValueError("selected revolve operation lacks its actual D1 or axis")
    Untouched, Result = DocumentValue.bodies
    BodyValue = Result if Feature.operation is BooleanOp.KCutOperation else Untouched
    if BodyValue.final_feature_id != Feature.id:
        BodyValue = DesignBody(Result.id, Feature.name, Feature.id)
    return ProjectRevolve(
        ReplaceValue(
            DocumentValue,
            parameters=(Parameter,),
            sketches=(SketchValue,),
            selections=(AxisPick,),
            bodies=(BodyValue,),
            feature_timeline=(
                ReplaceValue(
                    Feature,
                    order=0,
                    operation=BooleanOp.KCreate,
                    input_feature_ids=(),
                    selection_ids=(AxisPick.id,),
                ),
            ),
        )
    )


# the complete ownership plan must reject extra neutral state before any native field can be allocated
def ProjectSelRev(DocumentValue: CadDocument) -> SelectedRevPlan:
    if type(CastValue(object, DocumentValue)) is not CadDocument:
        raise TypeError("selected revolve requires a neutral document")
    DocumentValue.assert_valid()
    if (
        DocumentValue.assembly is not None
        or DocumentValue.DrawingValue is not None
        or DocumentValue.brep is not None
        or DocumentValue.meshes
        or DocumentValue.brep_payloads
        or DocumentValue.materials
        or DocumentValue.diagnostics
        or DocumentValue.capabilities
        or DocumentValue.source.attributes
        or DocumentValue.schema_version != "1.0"
        or tuple(
            map(
                len,
                (
                    DocumentValue.configurations,
                    DocumentValue.support_planes,
                    DocumentValue.sketches,
                    DocumentValue.feature_timeline,
                    DocumentValue.parameters,
                    DocumentValue.selections,
                    DocumentValue.bodies,
                ),
            )
        )
        != (1, 1, 3, 3, 3, 4, 2)
    ):
        raise ValueError("selected revolve requires two stocks and one complete cut")
    if DocumentValue.support_planes[0].provenance is not None:
        raise ValueError("selected revolve support has an unsupported source owner")
    Chosen = ReadStockIndex(DocumentValue)
    First, Second, Cutter = tuple(
        ProjectRevOp(DocumentValue, Feature, SketchValue)
        for Feature, SketchValue in zip(
            DocumentValue.feature_timeline, DocumentValue.sketches, strict=True
        )
    )
    Plans = (First, Second, Cutter)
    if (
        len({Value.ParameterId for Value in Plans}) != 3
        or len({Value.SelectionId for Value in Plans}) != 3
        or len({Value.AxisEntityId for Value in Plans}) != 3
        or DocumentValue.feature_timeline[2].selection_ids[1]
        in {Value.SelectionId for Value in Plans}
    ):
        raise ValueError("selected revolve repeats an actual driver or selection owner")
    CheckCutBands(*Plans)
    return SelectedRevPlan(Plans, Chosen)
