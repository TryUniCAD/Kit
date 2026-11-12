from convert.formats.Fusion.ContainerCodec.ContainerLayout import KMaxProperties
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.formats.Fusion.ContainerCodec.Wire.EmitAssetHeader import EmitAssetHeader
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)


def ReadAssetHeader(Payload: bytes) -> AssetHeader:
    Cursor = OpenWireCursor(Payload)
    if Cursor.ReadText(True) != KAssetName:
        raise ValueError("Unsupported Fusion asset name")
    AssetId, SnapshotId = Cursor.ReadGuid(), Cursor.ReadGuid()
    if (Cursor.ReadText(), Cursor.ReadWord()) != (KAssetRole, KWireVersion):
        raise ValueError("Unsupported Fusion asset header")
    Versions = Cursor.ReadVersions(KAssetKeys)
    if (Cursor.ReadText(), Cursor.ReadWord(), Cursor.TakeBytes(1)) != (
        KAssetKind,
        0,
        b"\0",
    ):
        raise ValueError("Unsupported Fusion asset property header")
    Properties = tuple(
        (Cursor.ReadText(), Cursor.ReadText(True))
        for _ in range(Cursor.ReadCount(KMaxProperties))
    )
    if Cursor.ReadWord() != 0:
        raise ValueError("Unsupported Fusion asset segment header")
    NextSegmentId = Cursor.ReadWord()
    Segments = tuple(
        SegmentSlot(
            Cursor.ReadWord(), SegmentKind(Cursor.ReadText()), Cursor.ReadText()
        )
        for _ in range(Cursor.ReadCount(3))
    )
    Cursor.CheckEnd()
    Result = AssetHeader(
        AssetId, SnapshotId, Versions, NextSegmentId, Segments, Properties
    )
    _ = EmitAssetHeader(Result)
    return Result
