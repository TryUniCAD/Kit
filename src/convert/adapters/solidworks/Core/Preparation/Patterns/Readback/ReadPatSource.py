from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatMap import ReadPatMap
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ReadPatHist import (
    ReadPatHist,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ReadPatSk import (
    ReadPatSk,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ReadPatSteps import (
    ProjectPatStep,
    ProjectPatStock,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# the construction copy feeds typed inputs while publication separately verifies every field of the unchanged source
def ReadPatSource(DocumentValue: CadDocument, NameValue: str) -> CadDocument:
    DocumentValue.assert_valid()
    (ConfigValue,) = DocumentValue.configurations
    (BodyValue,) = DocumentValue.bodies
    Plate, SeedValue, Hinge, Angle, Pattern = ReadPatHist(DocumentValue)
    Drivers = ReadPatMap(DocumentValue.parameters)
    PicksById = ReadPatMap(DocumentValue.selections)
    BaseStep, FirstDepth, _ = ProjectPatStock(Plate, Drivers, None)
    SeedStep, SecondDepth, SeedPick = ProjectPatStock(SeedValue, Drivers, Plate)
    PatternStep, Pitch, BodyPick = ProjectPatStep(Pattern, SeedValue, Drivers)
    if SeedPick is None:
        raise ValueError("SOLIDWORKS cold pattern lacks its actual merged seed")
    ParameterValues = {Value.id: Value for Value in (FirstDepth, SecondDepth, Pitch)}
    Choices = tuple(
        ReplaceValue(
            PicksById[ChoiceId],
            query=FreezeMapping(),
            provenance=None,
            attributes=FreezeMapping(),
        )
        for StepValue in (Hinge, Angle, Pattern)
        for ChoiceId in StepValue.selection_ids
    )
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(ConfigValue, attributes=FreezeMapping()),),
        parameters=tuple(
            (
                ParameterValues[Value.id]
                if Value.id in ParameterValues
                else ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            )
            for Value in DocumentValue.parameters
        ),
        support_planes=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in DocumentValue.support_planes
        ),
        sketches=tuple(ReadPatSk(Value) for Value in DocumentValue.sketches),
        selections=(*Choices, SeedPick, BodyPick),
        feature_timeline=(
            BaseStep,
            SeedStep,
            ReplaceValue(
                Hinge, input_feature_ids=(), provenance=None, attributes=FreezeMapping()
            ),
            ReplaceValue(
                Angle,
                input_feature_ids=(Hinge.id,),
                provenance=None,
                attributes=FreezeMapping(),
            ),
            PatternStep,
        ),
        bodies=(
            ReplaceValue(
                BodyValue,
                topology=TopologyCounts(),
                provenance=None,
                attributes=FreezeMapping(),
            ),
        ),
        brep=None,
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
    )
