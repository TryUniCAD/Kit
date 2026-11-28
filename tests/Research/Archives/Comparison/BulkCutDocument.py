from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Research.Archives.Comparison.BulkControls import MakeControls
from tests.Research.Archives.Comparison.BulkModifier import BindModifier
from tests.Research.Archives.Comparison.BulkTypedDocuments import MakeOutputDoc


# cut operands require a real earlier producer and exact owned extent controls
def MakeCutDoc(Prefix: str, Change: str) -> CadDocument:
    Document = MakeOutputDoc(Prefix)
    Controls = MakeControls(Prefix)
    BodyValue = Document.bodies[int(Change == "target")]
    Definition = DistanceCut(
        DistanceExtrude(
            Controls[int(Change == "parameter")].id, SpaceVector(0.0, 0.0, 1.0)
        ),
        (BodyValue.id,),
    )
    Feature = FeatureStep(
        Prefix + "modifier",
        "authored cut",
        FeatureKind.KExtrusion,
        2,
        (Document.feature_timeline[-1].id,),
        sketch_id=Document.sketches[0].id,
        parameter_ids=tuple(Control.id for Control in Controls),
        operation=BooleanOp.KCutOperation,
        definition=Definition,
        OutputBodyIds=(BodyValue.id,),
    )
    return BindModifier(Document, Feature, Controls)
