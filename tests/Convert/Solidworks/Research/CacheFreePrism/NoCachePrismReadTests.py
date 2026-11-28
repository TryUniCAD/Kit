from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from tests.Convert.Solidworks.Research.CacheFreePrism.CheckPrismDoc import CheckPrismDoc
from tests.Convert.Solidworks.Research.CacheFreePrism.MakeReadPrism import MakeReadPrism
from tests.Convert.Solidworks.Research.CacheFreePrism.RejectPrism import (
    RejectPrism,
)
from tests.Convert.Solidworks.Research.CacheFreePrism.ReversePrism import ReversePrism


# archive preparation and strict read must agree on independent rectangles while unsupported physical caches and ends remain rejected
def TestNoCacheRead() -> None:
    CasesValue = (
        ("NoCacheFirst", 23.625, 17.25, 8.875),
        ("NoCacheSecond", 41.5, 9.125, 16.375),
    )
    for NameValue, WidthValue, HeightValue, DepthValue in CasesValue:
        BytesValue = MakeReadPrism(NameValue, WidthValue, HeightValue, DepthValue)
        CheckPrismDoc(BytesValue, WidthValue, HeightValue, DepthValue)
        RejectPrism(ReversePrism(BytesValue))
        Archive = SldprtArchive.from_bytes(BytesValue)
        for StreamName, BufferValue in (
            ("Contents/Config-0-Partition", b""),
            ("Contents/Config-0-Partition", b"corrupt"),
            ("Contents/UnqualifiedGeometry", b"unrecognized"),
        ):
            StreamsValue = Archive.streams
            StreamsValue[StreamName] = BufferValue
            RejectPrism(BuildSldprt(StreamsValue, FormatVersion=4))
