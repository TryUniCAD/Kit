from convert.adapters.solidworks.Container.Format import (
    KeywordsStream,
    KResolvedFeaturesStream,
)


# the qualified offset container publishes metadata before the linked model definitions and manager header
def OrderOffStreams(StreamsValue: dict[str, bytes]) -> dict[str, bytes]:
    OrderValue = (
        "Header2",
        "_MO_VERSION_19000/Biography",
        "_MO_VERSION_19000/History",
        "Contents/Config-0-ModelHeader",
        KeywordsStream,
        "Contents/Config-0",
        "Contents/CMgr",
        "Contents/Definition",
        KResolvedFeaturesStream,
        "Contents/CMgrHdr2",
    )
    if set(StreamsValue) != set(OrderValue):
        raise ValueError("offset container requires its exact owned stream inventory")
    return {NameValue: StreamsValue[NameValue] for NameValue in OrderValue}
