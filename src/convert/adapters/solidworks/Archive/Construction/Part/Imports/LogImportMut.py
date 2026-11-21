from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the local body event must advance both model holders and log its actual feature identity
def LogImportMut(
    FeatureValue: ArchiveNode,
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    InputValue: HeaderInput,
) -> int:
    ActiveHeader, TopHeader, _ = HeadersValue
    StartStamp = FieldInt(ActiveHeader.FieldsValue, "f44")
    if (
        StartStamp != FieldInt(TopHeader.FieldsValue, "f44")
        or not 0 <= StartStamp < 0x7FFFFFFF
    ):
        raise ValueError("local body needs the same initial stamp in both headers")
    BodyStamp = StartStamp + 1
    for HeaderValue in (ActiveHeader, TopHeader):
        LogsValue = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f20"])
        ItemsValue = LogsValue.FieldsValue["items"]
        if not isinstance(ItemsValue, tuple):
            raise ValueError("local body header needs its ordered creation log")
        LogsValue.FieldsValue["items"] = (
            *ItemsValue,
            MakeRootLog(FeatureValue, InputValue),
        )
        HeaderValue.FieldsValue["f44"] = BodyStamp
    return BodyStamp
