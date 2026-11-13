from dataclasses import replace as ReplaceValue

from pytest import importorskip as ImportSkip
from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Author.BuildBundle import BuildBundle
from convert.formats.Fusion.DrawingCodec.Author.BuildDrawing import BuildDrawing
from convert.formats.Fusion.DrawingCodec.Author.MakeIdentity import MakeIdentity
from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec
from convert.formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from tests.convert.formats.FusionCodec.Drawings.DwgAuthorTests import (
    KDimension,
    KLayoutHandle,
    KViews,
    MakeDraft,
)

KDesign = DesignTarget(
    DisplayName="Kit Bracket",
    AssetId="a1a1a1a1-b2b2-4c3c-8d4d-e5e5e5e5e5e5",
    SnapshotId="b1b1b1b1-c2c2-4d3d-8e4e-f5f5f5f5f5f5",
    ChangeGuid="c1c1c1c1-d2d2-4e3e-8f4f-a5a5a5a5a5a5",
    ComponentGuid="d1d1d1d1-e2e2-4f3f-8a4a-b5b5b5b5b5b5",
    BodyPersistentId="e1e1e1e1-f2f2-4a3a-8b4b-c5c5c5c5c5c5",
    InstanceId=7,
    ComponentId=8,
    BodiesId=9,
    SketchesId=10,
)
KDatabaseName = "ExtFile.f1f1f1f1-a2a2-4b3b-8c4c-d5d5d5d5d5d5.dwg"
KDesignData = b"PK\x05\x06" + bytes(18)


def MakeSpec() -> DrawingSpec:
    return DrawingSpec(
        "Kit Bracket Drawing",
        KDesign,
        SheetSpec("Kit Sheet"),
        MakeIdentity(),
        KLayoutHandle,
    )


def TestFreshIds() -> None:
    First, Second = MakeIdentity(), MakeIdentity()
    assert First.DocumentId != Second.DocumentId
    assert First.DrawingFile != Second.DrawingFile
    assert len(First.DrawingToken) == 22


def TestNewBundle() -> None:
    Codec = ImportSkip("compression.zstd")
    Content = AuthorDwg(MakeDraft(KViews, (KDimension,)))
    SpecValue = MakeSpec()
    Drawing = BuildDrawing(SpecValue, DrawingDatabase(KDatabaseName, Content))
    Bundle = BuildBundle(SpecValue, Drawing, KDesignData)
    Emitted = EmitDrawBundle(Bundle, Codec.compress)

    def InflateZstd(Packed: bytes, Expected: int) -> bytes:
        Result = Codec.decompress(Packed)
        assert isinstance(Result, bytes) and len(Result) == Expected
        return Result

    Again = ReadDrawBundle(Emitted, InflateZstd)
    Database = Again.Drawing.Database
    assert Database is not None
    assert Database.FileName == KDatabaseName
    assert Database.Content == Content
    assert Again.Description.DesignName == "Kit Bracket Drawing"
    assert [Entry.DataValue for Entry in Again.Documents] == [KDesignData]


def TestSpecRejects() -> None:
    Database = DrawingDatabase(KDatabaseName, AuthorDwg(MakeDraft()))
    with ExpectError(ValueError, match="ExtFile"):
        _ = BuildDrawing(MakeSpec(), DrawingDatabase("Drawing.dwg", Database.Content))
    Broken = ReplaceValue(KDesign, AssetId="NOT-A-GUID")
    with ExpectError(ValueError, match="GUID"):
        _ = BuildDrawing(ReplaceValue(MakeSpec(), Design=Broken), Database)
    Drawing = BuildDrawing(MakeSpec(), Database)
    with ExpectError(ValueError, match="design bytes"):
        _ = BuildBundle(MakeSpec(), Drawing, b"")
