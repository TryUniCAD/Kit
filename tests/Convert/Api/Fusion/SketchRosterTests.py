from io import BytesIO as ByteStream
from zipfile import ZipFile

from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.Formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Sketches.SketchPlacement import KSketchBase
from tests.Convert.Api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.Convert.FusionRead import OpenResearch
from interchange.Enums.EnumFeatures import FeatureKind


# a repeated native child must invalidate coverage even when all primitive backlinks survive
@KRequiresCodec
def TestRoster() -> None:
    Archive = KStudyPath / "extents-f0f33a9a605f/distance_positive.f3d"
    (SketchValue,) = OpenResearch(Archive, StrictMode=False).sketches
    Members = SketchValue.attributes["fusion.geometry_child_ids"]
    assert IsObjectTuple(Members) and len(Members) == 3
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
    Document = OpenResearch(Stream, StrictMode=False)
    (Partial,) = Document.sketches
    assert Document.feature_timeline[0].kind == FeatureKind.KNative
    assert Partial.entities == SketchValue.entities
    assert "fusion.geometry_child_ids" not in Partial.attributes


# the native solver fixes the selected corner while keeping the coincident origin independent
@KRequiresCodec
def TestFixedCorner() -> None:
    Controls = KStudyPath.parent / "LocalOracle/RectangleConstraints"
    for Sample, Expected in (("Orientation4.f3d", False), ("FixedAnchor.f3d", True)):
        (SketchValue,) = OpenResearch(Controls / Sample, StrictMode=False).sketches
        Points = {Value.id: Value for Value in SketchValue.entities}
        Origin = Points["fusion-sketch-entity-205"]
        Corner = Points["fusion-sketch-entity-228"]
        assert Origin.geometry == Corner.geometry
        assert Origin.fixed and Origin.attributes["fusion.point_is_origin"] is True
        assert (
            Corner.fixed is Expected
            and Corner.attributes["fusion.point_is_origin"] is False
        )
