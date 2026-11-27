from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import EmptyFields, RequireFields


# unqualified fillet variants must refuse before constant radius semantics can reach public projection
def CheckRimModes(Context: RimContext) -> None:
    RequireFields(
        Context.Feature,
        {
            "filletType": 0,
            "isRollingBallCorners": True,
            "isSheetMetalFillet": False,
            "isTangentPropagation": True,
            "rParamRadius": None,
            "scopeOption": 0,
            "topologyOption": 0,
        },
    )
    RequireFields(
        Context.EdgeData,
        {
            "bAsymmetric": False,
            "bChord": False,
            "bFlip": False,
            "bG2Blend": False,
            "bRuleFillet": False,
            "bConstantRadius": True,
            "bIsComputeChain": True,
            "scopeOption": 0,
            "topologyOption": 0,
            "selSetIndex": 0,
        },
    )
    RequireFields(
        Context.EdgeData,
        {
            NameValue: None
            for NameValue in (
                "chordLen",
                "curveChainStartPoint",
                "edgeOffset1Value",
                "edgeOffset2Value",
                "rFaceRef",
                "rFeatureRef",
                "rFullRoundRef",
                "rRuleRef",
            )
        },
    )
    EmptyFields(
        Context.EdgeData,
        ("edgeSequence", "midPointParams", "pointParams", "pointRadii"),
    )
