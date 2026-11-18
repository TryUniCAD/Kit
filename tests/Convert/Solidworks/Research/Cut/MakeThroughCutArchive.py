from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughPart import (
    MakeThroughPart,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe


# the complete constructor emits each test part from independently specified stock circle and through termination inputs
def MakeThroughCutArchive(AxisValue: str, Reverse: bool, Both: bool) -> bytes:
    Stock = ThroughStock(
        NameValue="GeneratedThroughCut",
        ConfigName="Default",
        PlaneName={"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}[AxisValue],
        SketchId="stock-sketch",
        SketchName="StockProfile",
        FeatureId="stock-boss",
        FeatureName="StockBoss",
        ParameterId="stock-depth",
        BodyId="cut-body",
        VerticesValue=(
            (-0.028, -0.018),
            (0.033, -0.018),
            (0.033, 0.021),
            (-0.028, 0.021),
        ),
        DepthValue=0.0143,
        WidthValue=0.061,
        HeightValue=0.039,
        AxisValue=AxisValue,
    )
    Inputs = ThroughPartSpec(
        Stock,
        CircleInput((0.0118, 0.0057), 0.0031, 19000),
        "ThroughProfile",
        "ThroughFeature",
        ThroughEndInput("through_all_both" if Both else "through_all", Reverse, 19000),
    )
    return MakeThroughPart(Inputs, MakePartRecipe(Stock, 1794001000)).BytesValue
