from io import BytesIO as ByteStream
from zipfile import ZipFile

from convert.Formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Sketches.SketchPlacement import KSketchBase
from tests.Convert.Api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.Convert.FusionRead import OpenResearch


# a repeated native child must invalidate coverage even when all primitive backlinks survive
@KRequiresCodec
def TestRoster() -> None:
    Archive = KStudyPath / "extents-f0f33a9a605f/distance_positive.f3d"
    (SketchValue,) = OpenResearch(Archive, StrictMode=False).sketches
    Members = SketchValue.attributes["fusion.geometry_child_ids"]
    assert isinstance(Members, tuple) and len(Members) == 3
    assert {f"fusion-sketch-entity-{Member}" for Member in Members} == {
        Entity.id for Entity in SketchValue.entities
    }
    BulkData, Spans = ReadDesignZip(Archive.read_bytes())
    (Continuation,) = (Value for Value in Spans if Value.ClassGuid == KSketchBase)
    Cursor = MetaCursor(
        BulkData[Continuation.PayloadOffset + 4 : Continuation.EndOffset]
    )
    Cursor.Offset = 28
    _ = Cursor.ReadText(True, Maximum=1024)
    assert Cursor.TakeBytes(1) == bytes(1) and Cursor.ReadWord() == 3
    Start = Continuation.PayloadOffset + 4 + Cursor.Offset
    Wrong = (
        BulkData[:Start] + BulkData[Start + 11 : Start + 22] + BulkData[Start + 11 :]
    )
    Stream = ByteStream()
    with ZipFile(Archive) as Original, ZipFile(Stream, "w") as Changed:
        for Entry in Original.infolist():
            Changed.writestr(
                Entry.filename,
                (
                    Wrong
                    if Entry.filename == KDesignPrefix + "BulkStream.dat"
                    else Original.read(Entry)
                ),
            )
    _ = Stream.seek(0)
    (Partial,) = OpenResearch(Stream, StrictMode=False).sketches
    assert Partial.entities == SketchValue.entities
    assert "fusion.geometry_child_ids" not in Partial.attributes
