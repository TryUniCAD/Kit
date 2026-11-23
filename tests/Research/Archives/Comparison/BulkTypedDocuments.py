from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordTopology import TopologyCounts
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# distinct body observations prevent fixture symmetry from selecting arbitrary body counterparts
def MakeOutputDoc(Prefix: str, Changed: bool = False) -> CadDocument:
    Document = MakeDocument(Prefix)
    Stock = Document.feature_timeline[-1]
    Bodies = tuple(
        DesignBody(
            Prefix + "body" + str(Index),
            "authored body",
            Stock.id,
            topology=TopologyCounts(volume=Volume),
        )
        for Index, Volume in enumerate((11.0, 23.0))
    )
    Stock = ChangeRecord(Stock, OutputBodyIds=(Bodies[int(Changed)].id,))
    return ChangeRecord(
        Document,
        bodies=Bodies,
        feature_timeline=(*Document.feature_timeline[:-1], Stock),
    )


# independently owned alternative controls make a changed dependency visible without changing scalar records
def MakeControls(Prefix: str) -> tuple[Parameter, ...]:
    return tuple(
        Parameter(
            Prefix + "distance" + str(Index),
            "authored distance",
            ParameterValue(Number, ValueKind.KLength, "mm"),
            owner_id=Prefix + "modifier",
        )
        for Index, Number in enumerate((0.5, 1.5))
    )


# live modifying histories must preserve the producer and terminal body ownership together
def BindModifier(
    Document: CadDocument,
    Feature: FeatureStep,
    Controls: tuple[Parameter, ...],
    Selections: tuple[Selection, ...] = (),
) -> CadDocument:
    Stock = ChangeRecord(
        Document.feature_timeline[-1],
        OutputBodyIds=tuple(BodyValue.id for BodyValue in Document.bodies),
    )
    return ChangeRecord(
        Document,
        parameters=(*Document.parameters, *Controls),
        selections=Selections,
        feature_timeline=(*Document.feature_timeline[:-1], Stock, Feature),
        bodies=tuple(
            (
                ChangeRecord(BodyValue, final_feature_id=Feature.id)
                if BodyValue.id in Feature.OutputBodyIds
                else BodyValue
            )
            for BodyValue in Document.bodies
        ),
    )


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


# dangling typed operands must reach document admission instead of silently becoming comparison edges
def LoseTypedRef(Document: CadDocument, RoleName: str) -> CadDocument:
    Feature = Document.feature_timeline[-1]
    if RoleName == "OutputBodyIds":
        Feature = ChangeRecord(Feature, OutputBodyIds=("missing",))
    elif isinstance(Feature.definition, DistanceCut):
        Feature = ChangeRecord(
            Feature,
            definition=ChangeRecord(Feature.definition, TargetBodyIds=("missing",)),
        )
    else:
        assert isinstance(Feature.definition, FaceOffset)
        Feature = ChangeRecord(
            Feature,
            definition=ChangeRecord(Feature.definition, **{RoleName: "missing"}),
        )
    return ChangeRecord(
        Document, feature_timeline=(*Document.feature_timeline[:-1], Feature)
    )
