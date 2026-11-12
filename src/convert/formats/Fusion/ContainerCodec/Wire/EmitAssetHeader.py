from typing import cast as CastValue

from convert.formats.Fusion.ContainerCodec.ContainerLayout import KMaxProperties
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.SegmentFolders import SegmentFolders
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KPhysicalKey,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)


def EmitAssetHeader(Value: AssetHeader) -> bytes:
    _ = SegmentFolders(Value)
    SinkValue = ManifestSink()
    SinkValue.AddText(KAssetName, WideText=True)
    SinkValue.AddGuid(Value.AssetId)
    SinkValue.AddGuid(Value.SnapshotId)
    SinkValue.AddText(KAssetRole)
    SinkValue.AddWord(KWireVersion)
    SinkValue.AddVersions(Value.Versions, KAssetKeys)
    SinkValue.AddText(KAssetKind)
    SinkValue.AddWord(0)
    SinkValue.AddBytes(b"\0")
    SinkValue.AddCount(Value.Properties, KMaxProperties)
    Names: set[str] = set()
    for Entry in Value.Properties:
        if (
            type(Entry) is not tuple
            or len(CastValue(tuple[object, ...], Entry)) != 2
            or type(Entry[0]) is not str
            or not Entry[0]
            or Entry[0] in Names
        ):
            raise ValueError("Invalid Fusion asset property")
        Names.add(Entry[0])
        SinkValue.AddText(Entry[0])
        if Entry[0] == KPhysicalKey:
            SinkValue.AddGuid(Entry[1])
        else:
            SinkValue.AddText(Entry[1], WideText=True)
    SinkValue.AddWord(0)
    SinkValue.AddWord(Value.NextSegmentId)
    SinkValue.AddWord(len(Value.Segments))
    for Entry in Value.Segments:
        SinkValue.AddWord(Entry.SegmentId)
        SinkValue.AddText(Entry.Segment.value)
        SinkValue.AddText(Entry.UserName)
    Payload = bytes(SinkValue.Buffer)
    if len(Payload) > KMaxManifestBytes:
        raise ValueError("Oversized Fusion asset manifest")
    return Payload
