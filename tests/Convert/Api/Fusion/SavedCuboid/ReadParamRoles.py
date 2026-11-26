from interchange import CadDocument
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Features.FeatureDistExt import DistanceExtrude


# each physical role must retain its parameter identity even if native object numbers change
def ReadParamRoles(Document: CadDocument) -> tuple[str, str, str, str]:
    Names = {Param.id: Param.name for Param in Document.parameters}
    Sketch = Document.sketches[0]
    ByAxis = {
        Entry.kind: Names[Entry.parameter_id]
        for Entry in Sketch.constraints
        if Entry.parameter_id is not None
    }
    Extent = Document.feature_timeline[-1].definition
    assert isinstance(Extent, DistanceExtrude) and Extent.TaperParameterId is not None
    return (
        ByAxis[ConstraintKind.KDistanceX],
        ByAxis[ConstraintKind.KDistanceY],
        Names[Extent.AlongParameterId],
        Names[Extent.TaperParameterId],
    )
