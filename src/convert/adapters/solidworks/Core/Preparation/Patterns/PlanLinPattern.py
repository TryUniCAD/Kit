from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.LinPatternInput import (
    LinPatternInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.JoinSeedBounds import (
    JoinSeedBounds,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatHinge import (
    CheckPatHinge,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatHistory import (
    CheckPatHistory,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatNames import (
    CheckPatNames,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatResult import (
    CheckPatResult,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatScope import (
    CheckPatScope,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatAngle import (
    ReadPatAngle,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatMap import ReadPatMap
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatPlanes import (
    ReadPatPlanes,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatPresent import (
    ReadPatPresent,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatStocks import (
    ReadPatStocks,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatTarget import (
    ReadPatTarget,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatValues import (
    ReadPatValues,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureBoundPlane import BoundDatum


# an internal write plan must join the complete portable history before archive construction
def PlanLinPattern(
    DocumentValue: CadDocument,
    TargetValue: SelfFileInput,
    PresentValue: PatPresentInput,
) -> LinPatternInput:
    ConfigValue = CheckPatScope(DocumentValue)
    NameValue = ReadPatTarget(DocumentValue, TargetValue)
    CheckPatHistory(DocumentValue)
    PlateStep, SeedStep, HingeStep, AngleStep, PatternStep = (
        DocumentValue.feature_timeline
    )
    DatumValue = AngleStep.definition
    if type(DatumValue) is not BoundDatum:
        raise ValueError("angled datum requires an actual bound definition")
    PlanesValue = ReadPatMap(DocumentValue.support_planes)
    SketchValues = ReadPatMap(DocumentValue.sketches)
    ParamValues = ReadPatMap(DocumentValue.parameters)
    PickValues = ReadPatMap(DocumentValue.selections)
    Front, TopPlane, Right, AnglePlane = ReadPatPlanes(
        PlanesValue, DatumValue.SupportPlaneId
    )
    PlateValue, SeedValue = ReadPatStocks(
        PlateStep, SeedStep, Front.id, SketchValues, ParamValues, PickValues
    )
    BoundsValue = JoinSeedBounds(PlateValue.BoundsValue, SeedValue.BoundsValue)
    CheckPatHinge(HingeStep, TopPlane.id, Right.id, PickValues, BoundsValue)
    ParamId, RadiansValue = ReadPatAngle(
        AngleStep, HingeStep.id, AnglePlane, Right, PickValues, ParamValues
    )
    CountValue, PitchValue, Reversed = ReadPatValues(
        PatternStep, SeedStep.id, AngleStep.id, AnglePlane, PickValues, ParamValues
    )
    CheckPatResult(DocumentValue.bodies[0], PatternStep, CountValue)
    CountId, PitchId = PatternStep.parameter_ids
    AngleInput = ReadPatPresent(
        PresentValue, AngleStep.name, RadiansValue, ParamId, CountId, PitchId
    )
    StockValue = SeedStockInput(
        NameValue,
        ConfigValue.name,
        TargetValue.PathName,
        TargetValue.SavedAt,
        PlateValue,
        SeedValue,
    )
    CheckPatNames(StockValue, HingeStep.name, AngleStep.name, PatternStep.name)
    return LinPatternInput(
        StockValue,
        HingeStep.name,
        AngleInput,
        PresentValue.AnnoValues,
        PresentValue.ActiveAnno,
        PresentValue.ShownAnnos,
        PatternStep.name,
        CountValue,
        PitchValue,
        Reversed,
        PresentValue.StyleValues,
    )
