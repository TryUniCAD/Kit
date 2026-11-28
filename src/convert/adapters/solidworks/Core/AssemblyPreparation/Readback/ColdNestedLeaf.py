from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ColdRectDriver import (
    ColdRectDriver,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# the strict part reader supplies either one blind depth or both independently owned rectangle distances
def ColdNestedLeaf(Document: CadDocument, NameValue: str) -> CadDocument:
    if not IsColdRead(Document):
        raise ValueError("reopened leaf requires the complete typed cold part")
    if len(Document.parameters) == 1:
        return ColdReadInput(Document, NameValue)
    if len(Document.sketches) != 1 or len(Document.parameters) != 3:
        raise ValueError("reopened leaf has an unsupported editable inventory")
    (SketchValue,) = Document.sketches
    if (
        SketchValue.attributes.get("typed_line_dimensions") is not True
        or len(SketchValue.parameter_ids) != 2
    ):
        raise ValueError("reopened leaf lacks the actual rectangle driver graph")
    (OwnerId,) = tuple(
        RowValue.id
        for RowValue in Document.feature_timeline
        if RowValue.sketch_id == SketchValue.id
        and RowValue.parameter_ids == SketchValue.parameter_ids
    )
    Drivers = tuple(
        ColdRectDriver(Document.parameter(ParamId), OwnerId, SketchValue.id)
        for ParamId in SketchValue.parameter_ids
    )
    DepthValues = tuple(
        ParamValue
        for ParamValue in Document.parameters
        if ParamValue.id not in SketchValue.parameter_ids
    )
    BareSketch = ReplaceValue(SketchValue, constraints=(), parameter_ids=())
    PartValue = ColdReadInput(
        ReplaceValue(Document, parameters=DepthValues, sketches=(BareSketch,)),
        NameValue,
    )
    Constraints = tuple(
        ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
        for Value in SketchValue.constraints
    )
    Profile = ReplaceValue(
        PartValue.sketches[0],
        constraints=Constraints,
        parameter_ids=SketchValue.parameter_ids,
    )
    return ReplaceValue(
        PartValue, sketches=(Profile,), parameters=(*PartValue.parameters, *Drivers)
    )
