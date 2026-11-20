from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSplitMut import ReadSplitMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# array prefixes retain their native words while item traversal uses the proven count rule
def ReadCountMut(FrameValue: ReadFrame, RuleValue: NativeField) -> int:
    Cursor = FrameValue.ReaderValue.Cursor
    Probe = BinaryReader(Cursor.BytesValue, Cursor.OffsetValue)
    CountName = RuleValue.CountValue or RuleValue.NameValue + "#count"
    WidthName = CountName + "#width"
    if RuleValue.TypeValue == "Split":
        RepeatCount, CountFields = ReadSplitMut(Probe, RuleValue, CountName)
    elif RuleValue.TypeValue in ("Count", "Framework"):
        IsFramework = RuleValue.TypeValue == "Framework"
        CountValue, Probe.OffsetValue = ReadCount(
            Probe.BytesValue, Probe.OffsetValue, IsFramework=IsFramework
        )
        RepeatCount = NormalizeCount(CountValue, RuleValue.ModeValue)
        CountFields = {CountName: CountValue}
        WidthValue = Probe.OffsetValue - Cursor.OffsetValue
        if WidthValue != len(EncodeCount(CountValue, IsFramework=IsFramework)):
            CountFields[WidthName] = WidthValue
    else:
        CountValue = CastValue(int, ReadScalarMut(Probe, RuleValue.TypeValue))
        RepeatCount = NormalizeCount(CountValue, RuleValue.ModeValue)
        CountFields = {CountName: CountValue}
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields.update(CountFields)
    if WidthName not in CountFields:
        _ = Fields.pop(WidthName, None)
    Cursor.OffsetValue = Probe.OffsetValue
    return RepeatCount
