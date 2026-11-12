from dataclasses import replace as Replace

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmText
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


@TestMarks.parametrize("HasHistory", (False, True))
def TestSourceLinks(HasHistory: bool) -> None:
    Sample = MakeSample()
    TagSet = Replace(Sample.TagSet, SideFace=FeatureTag(1, "3", (1701, 1702)))
    if HasHistory:
        Payload = EmitHistory(
            Sample.Model, Sample.Identity, TagSet, Sample.History, Sample.Stamp
        )
    else:
        Payload = EmitSnapshot(Sample.Model, TagSet, Sample.Stamp)
    Table = ReadAsmTable(Payload)
    Expected = {
        (Value.Selector, Value.Label, Value.Operations)
        for Value in (
            TagSet.SideFace,
            TagSet.TopFace,
            TagSet.BottomFace,
            TagSet.TopEdge,
            TagSet.BottomEdge,
        )
    }
    Observed: set[tuple[int, str, tuple[int, ...]]] = set()
    SketchCount = 0
    for Record in (
        Value for Value in Table.Records if Value.Name == "ATTRIB_CUSTOM-attrib"
    ):
        Owner = Table.Records[ReadAsmPtr(Record, 4)]
        Family = ReadAsmText(Record, 5)
        if Family == "sketch_attrib_def":
            SketchCount += 1
            Sense = (
                TagSet.Sketch.Sense
                if Owner.Name == "coedge"
                else 1 - TagSet.Sketch.Sense
            )
            Actual = tuple(int(Value) for Value in ReadAsmText(Record, 9).split())
            assert Actual == (
                TagSet.Sketch.Primary,
                TagSet.Sketch.Secondary,
                Sense,
                0,
                TagSet.Sketch.EnumA,
                TagSet.Sketch.EnumB,
            )
        elif Family == "generic_tag_attrib_def" and Owner.Name in ("face", "edge"):
            assert ReadAsmInt(Record, 10) == 1
            RefCount = ReadAsmInt(Record, 14)
            Operations = tuple(
                ReadAsmInt(Record, 15 + Index) for Index in range(RefCount)
            )
            Observed.add((ReadAsmInt(Record, 11), ReadAsmText(Record, 12), Operations))
    assert Observed == Expected
    assert SketchCount == (2 if HasHistory else 6)
