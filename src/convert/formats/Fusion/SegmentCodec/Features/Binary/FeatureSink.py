from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureBytes
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from typing_extensions import override as Override


class FeatureSink(MetaSink):
    __slots__ = ()

    @Override
    def AddBytes(self, Content: bytes) -> None:
        if len(self.Buffer) + len(Content) > KMaxFeatureBytes:
            raise ValueError("Oversized Fusion feature payload")
        super().AddBytes(Content)
