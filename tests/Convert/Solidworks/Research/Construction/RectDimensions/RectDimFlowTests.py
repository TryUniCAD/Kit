from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.Part.AssertPartBytes import (
    AssertPartBytes,
)
from tests.Convert.Solidworks.Research.Construction.RectDimensions.RectDimRequest import (
    RectDimRequest,
)
from tests.Convert.Solidworks.Research.Construction.RectDimensions.RunRectDimPhase import (
    RunRectDimPhase,
)


# complete neutral rectangle dimensions must survive actual serialization and fresh linked preparation with independent mathematical byte agreement
def TestRectDims() -> None:
    LengthValues: list[int] = []
    for NameValue, IsVariant in (
        ("sdk dimension alpha", False),
        ("sdk 寸法 beta translated", True),
    ):
        RequestValue = RectDimRequest(NameValue, IsVariant)
        BuildValue = RunRectDimPhase(RequestValue, "build")
        PacketValue: dict[str, object] = {"request": RequestValue, "build": BuildValue}
        Prepared = RunRectDimPhase(PacketValue, "prepare")
        Counterpart = RunRectDimPhase(PacketValue, "counterpart")
        AssertPartBytes(BuildValue, Prepared, Counterpart)
        assert BuildValue["next_id"] == 27
        assert BuildValue["dimension_ids"] == [19, 20]
        assert BuildValue["boss_dimension_ids"] == [22, 23, 24, 25, 26]
        for ReportValue in (BuildValue, Prepared):
            Dimensions = CastValue(dict[str, object], ReportValue["sketch_dimensions"])
            assert Dimensions["value_count"] == Dimensions["display_count"] == 2
            assert Dimensions["axis_relation_count"] == 4
            assert Dimensions["actual_sketch_handles"] is True
            assert Dimensions["constraint_reference_counts"] is True
        Rejections = CastValue(list[dict[str, object]], BuildValue["malformed"])
        assert len(Rejections) == 20 and all(
            RowValue["rejected"] for RowValue in Rejections
        )
        LengthValues.append(CastValue(int, BuildValue["bytes"]))
    assert LengthValues[0] != LengthValues[1]
