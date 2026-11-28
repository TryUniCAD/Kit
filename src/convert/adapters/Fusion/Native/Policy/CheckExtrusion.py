from convert.adapters.Fusion.Native.Graph.ReadExtentMode import ReadExtentMode
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Policy.CheckExtStart import CheckExtStart


# invalid extrusion input must fail here so public document claims remain grounded in native records
def CheckExtrusion(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    YzDatum: bool = False,
    Operation: int = 4,
    AllowOffset: bool = False,
) -> None:
    if Operation not in (2, 4):
        raise ValueError("Unsupported native modifying extrusion operation")
    Feature = Context.Extrude
    SideMode = ReadExtentMode(Feature)
    CheckExtStart(Graph, Context, AllowOffset)
    RequireFields(
        Feature,
        {
            "booleanOperation": Operation,
            "directionType": (
                1 if SideMode == "one_sided" else 2 if SideMode == "two_sided" else 3
            ),
            "extendFaceOption": 2 if SideMode == "one_sided" else 1,
            "isSolidOperation": True,
            "side1ExtentType": 1,
            "side1SolutionType": 0,
            "side2ExtentType": 1 if SideMode == "two_sided" else 0,
            "side2SolutionType": 0,
            "side2ExtendFaceOption": 0 if SideMode == "one_sided" else 1,
            "symmetricMeasurementType": (
                1
                if SideMode == "symmetric_full"
                else 2 if SideMode == "symmetric_half" else 0
            ),
        },
    )
    RequireFields(
        Feature,
        {
            NameValue: False
            for NameValue in (
                "isFlipDirection",
                "side2FlipDirection",
                "startDirectionFlip",
                "thinExtrude",
                "bIsAGDExtrudeFeature",
            )
        },
    )
    RequireFields(
        Feature,
        {
            NameValue: None
            for NameValue in (
                "ProfileFromEntityRef",
                "rFromEntityRef",
                "rToEntityRef",
                "side1Offset",
                "side2Offset",
                "thinExtrudeSide1WallThickness",
                "thinExtrudeSide2WallThickness",
            )
        },
    )
    if SideMode == "two_sided":
        _ = ResolveField(Graph, Feature, "rAgainstDistance", "DcDoubleParameter")
        _ = ResolveField(Graph, Feature, "side2TaperAngle", "DcDoubleParameter")
    else:
        RequireFields(Feature, {"rAgainstDistance": None})
        RequireFields(
            Feature,
            {
                "side2TaperAngle": (
                    Feature.Fields["rTaperAngle"]
                    if SideMode.startswith("symmetric_")
                    else None
                )
            },
        )
    EmptyFields(Feature, ("cachedDcBodies", "removedBodies"))
    if Operation == 4:
        EmptyFields(Feature, ("targetDataRefs",))
    SameNumbers(
        PointCoords(Feature.Fields["profileNormal"]),
        (1.0, 0.0, 0.0) if YzDatum else (0.0, 0.0, 1.0),
    )
    ToolBody = ResolveField(Graph, Feature, "rExtrudeToolBody", "DcExtrudeToolBody")
    if Graph.Resolve(ToolBody.Fields["rExtrudeFeature"]) != Feature:
        raise ValueError("Native extrusion tool references another feature")
