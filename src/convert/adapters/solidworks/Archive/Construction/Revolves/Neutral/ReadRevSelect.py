from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# a selected construction axis must identify the actual local sketch entity rather than a matching geometric cache
def ReadRevSelect(DocumentValue: CadDocument, DefinitionValue: AngularRevolve) -> str:
    FeatureValue = DocumentValue.feature_timeline[0]
    SketchValue = DocumentValue.sketches[0]
    Selection = DocumentValue.selections[0]
    if (
        FeatureValue.selection_ids != (Selection.id,)
        or DefinitionValue.AxisSelectionId != Selection.id
        or Selection.query
        or Selection.point is not None
        or Selection.attributes
        or len(Selection.path) != 2
        or Selection.path[0].entity_kind != "sketch"
        or Selection.path[0].entity_id != SketchValue.id
        or Selection.path[0].subelement != ""
        or Selection.path[1].entity_kind != "sketch_entity"
        or Selection.path[1].subelement != ""
    ):
        raise ValueError("revolve axis must select its actual local sketch entity")
    return Selection.path[1].entity_id
