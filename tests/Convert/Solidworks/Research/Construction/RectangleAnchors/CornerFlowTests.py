from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.CornerRequest import (
    CornerRequest,
)
from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.RunCornerPhase import (
    RunCornerPhase,
)


# origin anchoring must retain input dependent editable rectangle semantics across complete native graph and container process boundaries
def TestCornerFlow() -> None:
    HashValues: set[str] = set()
    for NameValue, LengthValue, WidthValue, DepthValue, IsVariant in (
        ("OriginSyntheticAlpha", 31.75, 18.125, 9.625, False),
        ("OriginSyntheticBeta", 14.375, 27.625, 6.875, True),
        ("F14aSizedDiscovery", 20.0, 30.0, 10.0, False),
    ):
        RequestValue = CornerRequest(
            NameValue, LengthValue, WidthValue, DepthValue, IsVariant
        )
        BuildValue = RunCornerPhase(RequestValue, "build")
        Repeated = RunCornerPhase(RequestValue, "build")
        assert BuildValue == Repeated
        PacketValue: dict[str, object] = {"request": RequestValue, "build": BuildValue}
        _ = RunCornerPhase(PacketValue, "prepare")
        Compared = RunCornerPhase(PacketValue, "counterpart")
        assert len(CastValue(dict[str, object], Compared["streams"])) == 10
        assert BuildValue["next_id"] == 27
        assert BuildValue["feature_count"] == 19
        Rejections = CastValue(list[dict[str, object]], BuildValue["rejections"])
        assert len(Rejections) == 14
        assert all(RowValue["rejected"] for RowValue in Rejections)
        assert all(RowValue["publication_unchanged"] for RowValue in Rejections)
        HashValues.add(CastValue(str, BuildValue["sha256"]))
    assert len(HashValues) == 3
