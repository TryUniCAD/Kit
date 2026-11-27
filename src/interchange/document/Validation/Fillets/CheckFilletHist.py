from typing import Mapping as TypeMap

from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.Fillets.ReadRimProfile import ReadRimProfile
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Fillets.CheckFilletPick import CheckFilletPick
from interchange.Features.Fillets.GetFilletVals import GetFilletVals
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Transform import KAxisZ
from interchange.Records.RecordParameter import Parameter


# body and predecessor ownership must agree before a circular rim query can resolve through history
def CheckFilletHist(
    StepValue: FeatureStep,
    Definition: RadiusFillet,
    Document: CadDocument,
    Features: TypeMap[str, FeatureStep],
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> None:
    BodyId, SourceId = CheckFilletPick(StepValue, Definition, Selections)
    Source = Features.get(SourceId)
    BodyValue = next((Value for Value in Document.bodies if Value.id == BodyId), None)
    if (
        Source is None
        or Source.order >= StepValue.order
        or Source.suppressed
        or not isinstance(Source.definition, DistanceExtrude)
    ):
        raise ValueError("radius fillet requires an existing prior distance extrusion")
    if (
        BodyValue is None
        or Source.OutputBodyIds != (BodyId,)
        or StepValue.OutputBodyIds != (BodyId,)
        or BodyValue.final_feature_id != StepValue.id
    ):
        raise ValueError(
            "radius fillet and predecessor must own the same final output body"
        )
    Extrusion = Source.definition
    if (
        Extrusion.Direction != KAxisZ
        or Extrusion.SideMode != "one_sided"
        or Extrusion.StartOffsetId is not None
    ):
        raise ValueError("radius fillet requires a positive canonical blind extrusion")
    Depth = GetDistValues(Source, Extrusion, Parameters)
    if (
        Depth.LowerMm != 0
        or Depth.UpperMm <= 0
        or Depth.TaperRadians != 0
        or Depth.SecondTaperRadians is not None
    ):
        raise ValueError("radius fillet requires an untapered profile plane start")
    Circle = ReadRimProfile(Document, Source, Features)
    Radius, _ = GetFilletVals(StepValue, Definition, Parameters, Selections)
    if Radius >= min(Circle.radius, Depth.UpperMm):
        raise ValueError(
            "radius fillet radius must fit its actual predecessor profile and depth"
        )
