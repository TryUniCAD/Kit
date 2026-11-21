from math import cos as CosValue, radians as RadianValue, sin as SinValue
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmInput import (
    MakeAsmInput,
)
from tests.Convert.Solidworks.Research.Construction.RectDimensions.RectDimRequest import (
    RectDimRequest,
)


# generated group probes must vary component counts rotations endpoint ownership and fixed anchors without opening native sources or sealed case specifications
def GroupCaseInput(CountValue: int, IsVariant: bool) -> dict[str, object]:
    NameValue = f"SdkPlanarGroup{CountValue}" + ("Beta" if IsVariant else "Alpha")
    AssemblyValue = CastValue(
        dict[str, object], MakeAsmInput(NameValue, IsVariant)["assembly"]
    )
    ChildValue = RectDimRequest(
        "SdkGroupPlate" + ("Beta" if IsVariant else "Alpha"), IsVariant
    )
    AngleValue = RadianValue(-29.0 if IsVariant else 17.0)
    AxisU = [CosValue(AngleValue), SinValue(AngleValue), 0.0]
    AxisV = [-SinValue(AngleValue), CosValue(AngleValue), 0.0]
    Coordinates = [0.01913 + IndexValue * 0.06719 for IndexValue in range(CountValue)]
    Occurrences = [
        {
            "name": f"SdkGroupPlate-{IndexValue + 1}",
            "origin": [Distance * AxisU[0], Distance * AxisU[1], 0.01313 * IndexValue],
            "u": AxisU,
            "v": AxisV,
        }
        for IndexValue, Distance in enumerate(Coordinates)
    ]
    FixedIndex = CountValue - 1 if IsVariant else 0
    Mates: list[dict[str, object]] = []
    FreeIndices = [
        IndexValue for IndexValue in range(CountValue) if IndexValue != FixedIndex
    ]
    if len(FreeIndices) >= 2:
        Mates.append(
            GroupMateRow(
                "parallel", "FreeParallel", FreeIndices[1], FreeIndices[0], "z"
            )
        )
    for IndexValue in FreeIndices:
        Mates.append(
            GroupMateRow(
                "coincident", f"Coincident{IndexValue + 1}", FixedIndex, IndexValue, "y"
            )
        )
        Mates.append(
            GroupMateRow(
                "parallel", f"Parallel{IndexValue + 1}", IndexValue, FixedIndex, "z"
            )
        )
    DistanceMate = GroupMateRow("distance", "Distance1", 0, CountValue - 1, "x")
    DistanceMate.update(
        distance_m=Coordinates[-1] - Coordinates[0],
        design_intent=False,
        selected_leader=0,
    )
    Mates.insert(1, DistanceMate)
    return {
        "assembly": AssemblyValue,
        "child": ChildValue,
        "occurrences": Occurrences,
        "mates": Mates,
        "fixed_occurrence": FixedIndex,
    }


# every test relationship must carry independently authored ordered occurrence indices and explicit actual principal datum axes
def GroupMateRow(
    KindValue: str, NameValue: str, FirstIndex: int, SecondIndex: int, AxisValue: str
) -> dict[str, object]:
    return {
        "kind": KindValue,
        "name": NameValue,
        "endpoints": [
            {"occurrence": FirstIndex, "axis": AxisValue},
            {"occurrence": SecondIndex, "axis": AxisValue},
        ],
    }
