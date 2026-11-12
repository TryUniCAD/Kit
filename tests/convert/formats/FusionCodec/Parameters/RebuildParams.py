from collections.abc import Callable
from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.FormulaDeps.ScopedParams import ReadPartScope
from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SegmentCodec.Parameters.EmitNumBinding import EmitNumBinding
from convert.formats.Fusion.SegmentCodec.Parameters.EmitNumeric import EmitNumeric
from convert.formats.Fusion.SegmentCodec.Parameters.EmitParamNames import EmitParamNames
from convert.formats.Fusion.SegmentCodec.Parameters.EmitParamOrder import EmitParamOrder
from convert.formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.formats.Fusion.SegmentCodec.Parameters.ReadNumBinding import ReadNumBinding
from convert.formats.Fusion.Topology.BodyScope import FindBodyScope
from convert.formats.Fusion.ZipHistory import ReadBulkHistory


def RebuildParams(
    Source: FilePath,
    ChangeValue: Callable[[NativeParam], NativeParam] | None = None,
) -> bytes:
    with ZipFile(Source) as Archive:
        BulkName = KDesignPrefix + "BulkStream.dat"
        MetaName = KDesignPrefix + "MetaStream.dat"
        BulkData = Archive.read(BulkName)
        MetaData = Archive.read(MetaName)
        Spans = ReadBulkSpans(BulkData, MetaData)
        Scope = ReadArchiveScope(BulkData, Spans)
        Records = RebuildRecords(BulkData, Spans, Scope, ChangeValue)
        NewBulk, NewMeta = EmitSegment(ReadMetaWire(MetaData), Records)
        if ChangeValue is None:
            assert NewBulk == BulkData
            assert NewMeta == MetaData
        Buffer = BytesIO()
        with ZipFile(Buffer, "w") as Output:
            for Entry in Archive.infolist():
                Content = (
                    NewBulk
                    if Entry.filename == BulkName
                    else NewMeta if Entry.filename == MetaName else Archive.read(Entry)
                )
                Output.writestr(Entry, Content)
        return Buffer.getvalue()


def ReadArchiveScope(BulkData: bytes, Spans: tuple[RecordSpan, ...]) -> ParamScope:
    Histories, _, _ = ReadBulkHistory(BulkData, Spans)
    (History,) = Histories
    _, Collection, Registry, Members, Names = ReadPartScope(
        BulkData, Spans, History, VerifyOrder=True
    )
    ComponentId = FindBodyScope(BulkData, Spans, History)
    assert ComponentId is not None
    return ParamScope(
        Collection.ObjectId,
        Registry.ObjectId,
        ComponentId,
        Members,
        tuple(Names.items()),
    )


def RebuildRecords(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Scope: ParamScope,
    ChangeValue: Callable[[NativeParam], NativeParam] | None,
) -> list[BulkRecord]:
    Replacements = {
        Scope.CollectionId: EmitParamOrder(Scope),
        Scope.RegistryId: EmitParamNames(Scope),
    }
    Records: list[BulkRecord] = []
    for SpanValue in Spans:
        Payload = BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
        Original = Payload
        if SpanValue.IsPrimary and SpanValue.ClassGuid == KParamGuid:
            assert Payload[:4] == bytes(4)
            Value = ReadNativeNum(Payload[4:])
            if ChangeValue is not None:
                Value = ChangeValue(Value)
            Payload = EmitNumeric(Value)
        elif (
            SpanValue.IsPrimary
            and SpanValue.ClassGuid == "D91D429C-1BB5-4640-B49F-69AF14F463E9"
        ):
            Payload = EmitNumBinding(ReadNumBinding(Payload))
        elif SpanValue.IsPrimary and SpanValue.ObjectId in Replacements:
            Payload = Replacements[SpanValue.ObjectId]
        if ChangeValue is None:
            assert Payload == Original
        Records.append(
            BulkRecord(
                SpanValue.TypeCode, SpanValue.ObjectId, SpanValue.IsPrimary, Payload
            )
        )
    return Records
