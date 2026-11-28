from convert.adapters.solidworks.Container.Format import (
    KeywordsStream,
    KResolvedFeaturesStream,
)

# the measured construction and strict readback recognize the same cache free inventory
KOffStreamOrder = (
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


# the qualified offset container publishes metadata before the linked model definitions and manager header
def OrderOffStreams(StreamsValue: dict[str, bytes]) -> dict[str, bytes]:
    if set(StreamsValue) != set(KOffStreamOrder):
        raise ValueError("offset container requires its exact owned stream inventory")
    return {NameValue: StreamsValue[NameValue] for NameValue in KOffStreamOrder}
