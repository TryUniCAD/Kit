from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseKeywords


# clear members isolate semantic keyword order from archive compression differences across platforms
def CheckKeyStreams(DefaultArchive: bytes, SourceArchive: bytes) -> None:
    DefaultPart = SldprtArchive.FromBytes(DefaultArchive)
    SourcePart = SldprtArchive.FromBytes(SourceArchive)
    assert (DefaultPart.file_id, DefaultPart.format_version) == (
        SourcePart.file_id,
        SourcePart.format_version,
    )
    DefaultStreams = DefaultPart.Streams
    SourceStreams = SourcePart.Streams
    assert DefaultStreams.keys() == SourceStreams.keys()
    assert {
        Stream
        for Stream, DataValue in DefaultStreams.items()
        if DataValue != SourceStreams[Stream]
    } == {KeywordsStream}

    DefaultConfigs, DefaultFeatures = ParseKeywords(DefaultStreams[KeywordsStream])
    SourceConfigs, SourceFeatures = ParseKeywords(SourceStreams[KeywordsStream])
    assert DefaultConfigs == SourceConfigs
    Changed = 0
    for DefaultFeature, SourceFeature in zip(
        DefaultFeatures, SourceFeatures, strict=True
    ):
        if [Dimension.name for Dimension in DefaultFeature.dimensions] == [
            "width_mm",
            "height_mm",
        ]:
            Width, Height = DefaultFeature.dimensions
            assert SourceFeature == ReplaceValue(
                DefaultFeature, dimensions=[Height, Width]
            )
            Changed += 1
        else:
            assert SourceFeature == DefaultFeature
    assert Changed == 1
