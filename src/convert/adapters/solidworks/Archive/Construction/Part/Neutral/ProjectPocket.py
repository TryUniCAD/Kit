from math import isclose as IsClose
from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import (
    CheckPartLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPocketBounds import (
    CheckPocketBounds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.IsCircDiameter import (
    IsCircDiameter,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.MakeBlindPlan import (
    MakeBlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PocketPlan import (
    PocketPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircGeom import (
    ReadCircGeom,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPocketDrives import (
    ReadPocketDrives,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import (
    RequireBossDef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireCutDef import (
    RequireCutDef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    CheckPartScope,
)
from interchange.document.Models.DocumentModel import CadDocument


# the part plan consumes both ordered extrusions and each actual driving dimension
def ProjectPocket(DocumentValue: CadDocument) -> PocketPlan:
    CheckPartScope(DocumentValue, (2, 3), HistoryCount=2)
    PlaneValue = CheckPartLinks(DocumentValue)
    ScaleValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(DocumentValue.units)
    if ReadPrincAxis(PlaneValue.transform) != "z" or ScaleValue is None:
        raise ValueError(
            "ordinary pocket requires canonical front support and modeled units"
        )
    BossValue, CutValue = DocumentValue.feature_timeline
    BossSketch, CutSketch = DocumentValue.sketches
    BossDef = RequireBossDef(BossValue)
    CutDef = RequireCutDef(CutValue, BossValue.id)
    BossParam, CutParam, RadialParam = ReadPocketDrives(DocumentValue)
    if BossDef.length != BossParam.value or CutDef.length != CutParam.value:
        raise ValueError("pocket depth parameters must match their actual extrusions")
    VerticesValue = ReadRectSketch(BossSketch, ScaleValue)
    CircleValue = ReadCircGeom(CutSketch, ScaleValue)
    RadialMode: Literal["radius", "diameter"] | None = None
    if RadialParam is None:
        if CutSketch.constraints:
            raise ValueError(
                "an undimensioned pocket circle requires its unconstrained sketch"
            )
    else:
        IsDiameter = IsCircDiameter(CutSketch, CutSketch.entities[0].id, RadialParam.id)
        RadialMode = "diameter" if IsDiameter else "radius"
        if not IsClose(
            ReadLength(RadialParam.value),
            CircleValue.RadiusValue * (2 if IsDiameter else 1),
            rel_tol=1e-12,
            abs_tol=1e-14,
        ):
            raise ValueError("pocket radial driver must match its actual circle")
    PlanValue = PocketPlan(
        MakeBlindPlan(
            DocumentValue,
            VerticesValue,
            BossParam.id,
            ReadLength(BossDef.length),
            BossParam.name,
        ),
        CutSketch.name,
        CutValue.name,
        CircleValue,
        BossEndInput(ReadLength(CutDef.length), True, 19000, "blind"),
        RadialMode,
    )
    CheckPocketBounds(PlanValue)
    return PlanValue
