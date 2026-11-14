from __future__ import annotations as Annotations
from collections.abc import Mapping
from pathlib import Path as FilePath
import hashlib as Hashlib
import re as RegexLib
from typing import cast as CastValue

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams
from convert.adapters.nx.Format import KInfoValue
from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.Reader import DocDigest
from convert.adapters.nx.Splm import KAbsentFooter, KChecksumOffset, KHeaderRegion
from convert.adapters.nx.SplmBuild import DirectoryLength
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams
from convert.adapters.nx.Xxh32 import HashXxh
from interchange import (
    BrepPayload,
    CadDocument as CadDoc,
    Diagnostic as DiagnosticInfo,
    Severity,
    frozen_mapping as FrozenMapping,
)

# the native document format id remains stable across reader and writer
KFormatId = KInfoValue.format_id


# the writer only rewrites documents that retain an nx native container
KNativeDocKind = "native-document"

# the part suffix is the only accepted nx destination extension
KPartSuffix = ".prt"


# support accepts only native nx documents with one retained source container
def CanSupportNx(DocValue: CadDoc, Target: KTargetType) -> bool:
    if isinstance(Target, (str, FilePath)):
        if FilePath(Target).suffix.casefold() != KPartSuffix:
            return False
    elif not IsBinaryTarget(Target):
        return False
    Payload = NativePayload(DocValue)
    return (
        Payload is not None
        and Payload.data is not None
        and Payload.data.startswith(b"SPLMSSTR")
    )


# native payload lookup preserves one exact source container for replay
def NativePayload(DocValue: CadDoc) -> BrepPayload | None:
    for Payload in DocValue.brep_payloads:
        if (
            Payload.format_id == KFormatId
            and Payload.kind == KNativeDocKind
            and Payload.data is not None
        ):
            return Payload
    return None


# self references name the saved part so only other parts require companion files
def FindNeeds(DocValue: CadDoc) -> tuple[str, ...]:
    if DocValue.assembly is not None:
        return ("referenced NX component files",)
    References = DocValue.metadata.get("nx.external_references")
    if not isinstance(References, (tuple, list)):
        return ()
    ReferenceValues = CastValue(tuple[object, ...], References)
    SourceName = FilePath(DocValue.source.path).name.casefold()
    Others = [
        ReferenceText
        for ReferenceText in ReferenceValues
        if isinstance(ReferenceText, str)
        and FilePath(ReferenceText).name.casefold() not in ("", SourceName)
    ]
    return ("referenced NX component files",) if Others else ()


# reports need a plain flag because metadata values are untyped at the boundary
def HasEntries(Value: object) -> bool:
    return isinstance(Value, Mapping) and bool(
        CastValue(Mapping[object, object], Value)
    )


# writing rebuilds the nx container from its parsed stream map instead of copying
def WriteNx(
    DocValue: CadDoc, Target: KTargetType, Options: WriteOptions | None = None
) -> WriteResult:
    Settings = Options or WriteOptions()
    if Settings.validate:
        DocValue.assert_valid()
    CheckNeutral(DocValue)
    Payload = NativePayload(DocValue)
    if Payload is None or Payload.data is None:
        raise ValueError("NX writing requires a retained native NX document")
    if not Payload.data.startswith(b"SPLMSSTR"):
        raise ValueError("NX writing requires a modern SPLMSSTR source")
    Overrides = MakeOverrides(DocValue, Payload.data)
    DataValue = RebuildNative(Payload.data, Overrides)
    CheckOutput(DataValue, Payload.data)
    CheckSeals(DataValue)
    PathValue = WriteBytesMut(Target, DataValue, Settings.overwrite)
    Requirements = FindNeeds(DocValue)
    AttributesRequested = DocValue.metadata.get("nx.attribute_overrides")
    StreamsRequested = DocValue.metadata.get("nx.stream_overrides")
    Metadata = {
        "mode": "native_container_rewrite",
        "compatibility": "native-stream-rewrite",
        "container": DocValue.metadata.get("nx.container", "SPLMSSTR"),
        "native_geometry": True,
        "native_history": True,
        "native_parameters": True,
        "native_self_contained": not Requirements,
        "attribute_overrides": HasEntries(AttributesRequested),
        "stream_overrides": HasEntries(StreamsRequested),
        "source_sha256": Payload.sha256,
        "output_sha256": Hashlib.sha256(DataValue).hexdigest(),
        "referenced_files_written": 0,
        "application_usable": True,
        "vendor_loadable": True,
    }
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(DocValue), key=lambda Value: Value.value)
    )
    return WriteResult(
        PathValue,
        KFormatId,
        len(DataValue),
        diagnostics=(
            *DocValue.diagnostics,
            DiagnosticInfo(
                "nx.native_stream_rewrite",
                "The NX container is rebuilt from parsed streams; neutral geometry and parameters are not authored into new NX feature records.",
                Severity.INFO,
            ),
        ),
        metadata=FrozenMapping(Metadata),
        transfers=Transfers,
        requirements=Requirements,
        application_usable=True,
        vendor_loadable=True,
    )


# neutral edits must fail explicitly because the writer only replays native data
def CheckNeutral(DocValue: CadDoc) -> None:
    Expected = DocValue.metadata.get("nx.neutral_signature")
    if Expected is None:
        return
    if Expected != DocDigest(DocValue):
        raise ValueError(
            "NX writing does not support neutral feature or parameter edits"
        )


# container rebuilding recomputes the modern directory from parsed streams
def RebuildNative(DataValue: bytes, Overrides: dict[str, bytes]) -> bytes:
    return RebuildSplm(ReadSplm(DataValue), Overrides)


# overrides combine native attribute edits with whole stream replacement
def MakeOverrides(DocValue: CadDoc, DataValue: bytes) -> dict[str, bytes]:
    Overrides = {
        PathValue.removeprefix("/Root/"): Value
        for PathValue, Value in RawOverrides(DocValue).items()
    }
    Requested = DocValue.metadata.get("nx.attribute_overrides")
    if Requested is None:
        return Overrides
    if not isinstance(Requested, Mapping):
        raise ValueError("NX attribute overrides must be a mapping")
    Streams = (
        {
            PathValue.removeprefix("/Root/"): Value
            for PathValue, Value in SplmStreams(ReadSplm(DataValue))
        }
        if DataValue.startswith(b"SPLMSSTR")
        else {
            Stream.path: Stream.data for Stream in ReadStreams(ReadCompound(DataValue))
        }
    )
    Existing = Streams.get("part/attrs")
    if not Existing:
        raise ValueError("NX attribute overrides require a part attributes stream")
    Updated = Existing
    PartData = Streams.get("UG_PART/UG_PART")
    RequestedDict = CastValue(dict[object, object], Requested)
    for Title, Value in RequestedDict.items():
        if not isinstance(Title, str) or not isinstance(Value, str):
            raise ValueError("NX attribute overrides require string names and values")
        Updated = SwapAttribute(Updated, Title, Value)
        if PartData is not None:
            PartData = SwapNativeValue(PartData, Title, Value)
    if "part/attrs" in Overrides:
        raise ValueError("NX stream overrides must not duplicate attribute paths")
    Overrides["part/attrs"] = Updated
    if PartData is not None:
        if "UG_PART/UG_PART" in Overrides:
            raise ValueError("NX stream overrides must not duplicate attribute paths")
        Overrides["UG_PART/UG_PART"] = PartData
    return Overrides


# raw stream overrides let callers replace a whole native payload at any length
def RawOverrides(DocValue: CadDoc) -> dict[str, bytes]:
    Requested = DocValue.metadata.get("nx.stream_overrides")
    if Requested is None:
        return {}
    if not isinstance(Requested, Mapping):
        raise ValueError("NX stream overrides must be a mapping")
    Output: dict[str, bytes] = {}
    RequestedDict = CastValue(dict[object, object], Requested)
    for PathValue, Value in RequestedDict.items():
        if not isinstance(PathValue, str) or not isinstance(Value, (bytes, bytearray)):
            raise ValueError("NX stream overrides require a path and bytes")
        if not PathValue.startswith("/Root/"):
            raise ValueError("NX stream overrides must name a /Root/ path")
        Output[PathValue] = bytes(Value)
    return Output


# equal length replacement keeps directory sizes and checksummed header untouched
def SwapAttribute(DataValue: bytes, Title: str, Value: str) -> bytes:
    TitleBytes = Title.encode("utf-8")
    ValueBytes = Value.encode("utf-8")
    if b'"' in TitleBytes or b'"' in ValueBytes:
        raise ValueError("NX attribute names and values must not contain quotes")
    Pattern = RegexLib.compile(
        rb'<Attribute\b[^>]*\b(?:utf8title|title)="'
        + RegexLib.escape(TitleBytes)
        + rb'"[^>]*/?>'
    )
    Match = Pattern.search(DataValue)
    if Match is None:
        raise ValueError("NX attribute override names an unknown part attribute")
    Element = Match.group()
    Updated = Element
    for Field in (b"utf8value", b"value"):
        FieldPattern = RegexLib.compile(rb"\b" + Field + rb'="([^"]*)"')
        FieldMatch = FieldPattern.search(Updated)
        if FieldMatch is None:
            continue
        if len(FieldMatch.group(1)) != len(ValueBytes):
            raise ValueError("NX attribute overrides must preserve value byte length")
        Updated = (
            Updated[: FieldMatch.start(1)] + ValueBytes + Updated[FieldMatch.end(1) :]
        )
    if Updated == Element:
        raise ValueError("NX attribute override found no value fields")
    return DataValue[: Match.start()] + Updated + DataValue[Match.end() :]


# native object records carry a duplicate attribute value that nx reports
def SwapNativeValue(DataValue: bytes, Title: str, Value: str) -> bytes:
    TitleBytes = Title.encode("utf-8")
    ValueBytes = Value.encode("utf-8")
    Marker = DataValue.find(TitleBytes + b"\x00")
    if Marker < 0:
        return DataValue
    Start = Marker + len(TitleBytes) + 2
    EndValue = Start + len(ValueBytes)
    if EndValue > len(DataValue) or DataValue[EndValue : EndValue + 1] != b"\x00":
        return DataValue
    return DataValue[:Start] + ValueBytes + DataValue[EndValue:]


# rebuilt containers must carry both native seals so nx can validate the header
def CheckSeals(DataValue: bytes) -> None:
    if not DataValue.startswith(b"SPLMSSTR"):
        return
    Parsed = ReadSplm(DataValue)
    HeaderEnd = 0x19 + DirectoryLength(
        [
            (Entry.path, None)
            for Entry in Parsed.entries
            if Entry.region == KHeaderRegion
        ],
        KHeaderRegion,
    )
    SealIndex = HeaderEnd + KChecksumOffset
    FirstPayload = min(
        (Entry.offset for Entry in Parsed.entries if Entry.size), default=len(DataValue)
    )
    if SealIndex + 4 > min(FirstPayload, len(DataValue)):
        return
    StoredSeal = int.from_bytes(DataValue[SealIndex : SealIndex + 4], "little")
    if HashXxh(DataValue[0x19:SealIndex]) != StoredSeal:
        raise ValueError("rebuilt NX header seal is invalid")
    if Parsed.footer_offset == KAbsentFooter or len(DataValue) < 4:
        return
    StoredTail = int.from_bytes(DataValue[-4:], "little")
    if HashXxh(DataValue[Parsed.footer_offset : -4]) != StoredTail:
        raise ValueError("rebuilt NX footer seal is invalid")


# output validation reopens the rebuilt container and checks the part payload
def CheckOutput(DataValue: bytes, Source: bytes) -> None:
    if DataValue.startswith(b"SPLMSSTR"):
        ParsedSplm = ReadSplm(DataValue)
        Streams = {
            PathValue.removeprefix("/Root/"): Value
            for PathValue, Value in SplmStreams(ParsedSplm)
        }
    else:
        ParsedCompound = ReadCompound(DataValue)
        Streams = {Stream.path: Stream.data for Stream in ReadStreams(ParsedCompound)}
    PartData = Streams.get("UG_PART/UG_PART") or Streams.get("Root/UG_PART/UG_PART")
    if PartData is None:
        raise ValueError("rebuilt NX container lost its UG_PART payload")
    _ = ReadPayload(PartData)


# byte destinations keep the same short write protection as other adapters
def WriteBytesMut(
    Target: KTargetType, DataValue: bytes, Overwrite: bool
) -> FilePath | None:
    if isinstance(Target, (str, FilePath)):
        PathValue = FilePath(Target)
        with PathValue.open("wb" if Overwrite else "xb") as Handle:
            Count = Handle.write(DataValue)
        if Count != len(DataValue):
            raise OSError("incomplete NX file write")
        return PathValue
    if not IsBinaryTarget(Target):
        raise TypeError("NX requires a binary output stream")
    StreamCount = Target.write(DataValue)
    if StreamCount is not None and StreamCount != len(DataValue):
        raise OSError("incomplete NX stream write")
    return None
