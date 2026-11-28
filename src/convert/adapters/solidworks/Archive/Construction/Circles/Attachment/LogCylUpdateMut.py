from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import (
    MakeFeatTime,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# a modeled sequence of completed geometry owners advances both headers before attaching and tessellating
def LogCylUpdateMut(ChildValue: PartCandidate, WrittenAt: int) -> tuple[int, int]:
    HeaderValue, TopHeader = (
        ChildValue.HeaderValue.FieldsValue,
        ChildValue.TopHeader.FieldsValue,
    )
    StartStamp = FieldInt(HeaderValue, "f40")
    StartBody = FieldInt(HeaderValue, "f44")
    FeaturesValue = (
        ChildValue.SystemValue.OriginValue.ProfileValue,
        ChildValue.ProfileValue.ProfileValue,
        ChildValue.BossValue.FeatureValue,
    )
    RootValue = ChildValue.SystemValue.RootValue.FieldsValue
    BodyStamp, UpdateStamp = StartBody + 1, StartStamp + len(FeaturesValue)
    GeometryStamp = FieldInt(RootValue, "f1300") + len(FeaturesValue)
    if (StartStamp, StartBody) != (
        FieldInt(TopHeader, "f40"),
        FieldInt(TopHeader, "f44"),
    ) or not all(
        0 <= StampValue <= 0xFFFFFFFF
        for StampValue in (StartStamp, StartBody, BodyStamp, UpdateStamp, GeometryStamp)
    ):
        raise ValueError("concentric attachment header update stamps are inconsistent")
    for Position, NodeValue in enumerate(FeaturesValue, 1):
        FieldsValue = NodeValue.FieldsValue
        FieldsValue.update(MakeFeatTime(FeatureInstant(WrittenAt, Position)))
        FieldsValue.update(
            f29c=StartStamp + Position, f0c=FieldInt(FieldsValue, "f0c") & 0xFFFD7FF8
        )
    RootValue.update(f1300=GeometryStamp, f0c=FieldInt(RootValue, "f0c") & 0xFFFD7FF8)
    for FieldsValue in (HeaderValue, TopHeader):
        FieldsValue.update(f40=UpdateStamp, f44=BodyStamp, f48=WrittenAt)
    ChildValue.CurrentConfig.FieldsValue["f860"] = UpdateStamp
    return BodyStamp, UpdateStamp
