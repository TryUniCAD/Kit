from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Research.Archives.Comparison.BulkControls import MakeControls
from tests.Research.Archives.Comparison.BulkModifier import BindModifier
from tests.Research.Archives.Comparison.BulkTypedDocuments import MakeOutputDoc


# omitted face topology remains explicit while declared body selection and distance links stay comparable
def MakeOffsetDoc(Prefix: str, Change: str) -> CadDocument:
    Document = MakeOutputDoc(Prefix)
    Controls = MakeControls(Prefix)
    Selections = tuple(
        Selection(
            Prefix + "pick" + str(Index),
            "authored face pick",
            (
                SelectPathElem("body", BodyValue.id),
                SelectPathElem("face", "unresolved-face"),
            ),
            point=SpaceVector(float(Index), 0.0, 0.0),
        )
        for Index, BodyValue in enumerate((*Document.bodies, *Document.bodies))
    )
    BodyValue = Document.bodies[int(Change == "target")]
    Selected = Selections[int(Change == "target") + 2 * int(Change == "selection")]
    Definition = FaceOffset(
        BodyValue.id, Selected.id, Controls[int(Change == "parameter")].id
    )
    Feature = FeatureStep(
        Prefix + "modifier",
        "authored offset",
        FeatureKind.KOffset,
        2,
        (Document.feature_timeline[-1].id,),
        parameter_ids=tuple(Control.id for Control in Controls),
        definition=Definition,
        selection_ids=(Selected.id,),
        OutputBodyIds=(BodyValue.id,),
    )
    return ChangeRecord(
        BindModifier(Document, Feature, Controls, Selections),
        metadata={"kit.omitted_brep": True},
    )
