from __future__ import annotations

from dataclasses import replace as Replace
from hashlib import sha256 as Sha256
from pathlib import Path as FilePath

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumDocument import Severity
from interchange.enums.EnumUnits import UnitSystem
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordSource import CadSource
from interchange.core.Common import FreezeMapping

from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.creo.CreoFormat import CreoFormat
from convert.adapters.creo.Format import KFormatId
from convert.adapters.creo.Header import ReadHeader
from convert.adapters.creo.Toc import CreoEntry
from convert.adapters.creo.Toc import KMaxSectionBytes
from convert.adapters.creo.Toc import ReadSection
from convert.adapters.creo.Toc import ReadToc

KDefaultConfiguration = "Default"

KUnitByToken = {
    "mm": UnitSystem.KMillimeter,
    "m": UnitSystem.KMeter,
    "in": UnitSystem.KInch,
}


def SourceBytes(Source: KSourceType) -> tuple[bytes, str]:
    if isinstance(Source, (bytes, bytearray)):
        return (bytes(Source), "<memory>")
    if isinstance(Source, (str, FilePath)):
        PathValue = FilePath(Source).expanduser().resolve()
        return (PathValue.read_bytes(), str(PathValue))
    Reader = getattr(Source, "read", None)
    if not callable(Reader):
        raise TypeError("Creo source must be a path, bytes, or binary stream")
    TellMethod = getattr(Source, "tell", None)
    SeekMethod = getattr(Source, "seek", None)
    Position: int | None = None
    if callable(TellMethod) and callable(SeekMethod):
        PositionValue: object = TellMethod()
        if isinstance(PositionValue, int):
            Position = PositionValue
    ValueData = Reader()
    if Position is not None and callable(SeekMethod):
        _ = SeekMethod(Position)
    if not isinstance(ValueData, (bytes, bytearray)):
        raise TypeError("Creo source stream must be binary")
    return (bytes(ValueData), str(getattr(Source, "name", "<stream>")))


def ReadThumb(DataValue: bytes, Entries: tuple[CreoEntry, ...]) -> bytes | None:
    for EntryValue in Entries:
        if EntryValue.name != "THMB_IMG_MAIN":
            continue
        try:
            BodyData = ReadSection(DataValue, EntryValue)
        except CreoFormat:
            return None
        Start = BodyData.find(b"\xff\xd8\xff")
        if Start < 0:
            return None
        return BodyData[Start:]
    return None


def ThumbPayload(Thumb: bytes | None) -> tuple[BrepPayload, ...]:
    if Thumb is None or len(Thumb) > KMaxSectionBytes:
        return ()
    Value = BrepPayload(
        id="creo:thumbnail:1",
        format_id="jpeg",
        kind="thumbnail",
        schema="jpeg",
        sha256=Sha256(Thumb).hexdigest(),
        data=Thumb,
        source_stream="THMB_IMG_MAIN",
        role=PayloadRole.KAuxiliary,
        file_extension=".jpg",
    )
    return (Value,)


def ReadLengthUnit(
    DataValue: bytes, Entries: tuple[CreoEntry, ...]
) -> tuple[UnitSystem | None, str]:
    for EntryValue in Entries:
        if "UnitSystemDef" not in EntryValue.name:
            continue
        try:
            BodyData = ReadSection(DataValue, EntryValue)
        except CreoFormat:
            return (None, "")
        Marker = b"Offset\x00"
        Start = BodyData.find(Marker)
        if Start < 0:
            return (None, "")
        Tail = BodyData[Start + len(Marker) :]
        Token = Tail.split(b"\x00", 1)[0].decode("latin-1").strip()
        return (KUnitByToken.get(Token), Token)
    return (None, "")


def ValidateSections(
    DataValue: bytes, Entries: tuple[CreoEntry, ...]
) -> tuple[str, ...]:
    Failures: list[str] = []
    for EntryValue in Entries:
        if EntryValue.name == "THMB_IMG_MAIN":
            continue
        try:
            _ = ReadSection(DataValue, EntryValue)
        except CreoFormat as ErrorInfo:
            Failures.append(f"{EntryValue.name}: {ErrorInfo}")
    return tuple(Failures)


def SectionTable(
    Entries: tuple[CreoEntry, ...],
) -> tuple[tuple[str, int, int, int, str], ...]:
    return tuple(
        (
            EntryValue.name,
            EntryValue.offset,
            EntryValue.length,
            EntryValue.expanded,
            EntryValue.kind,
        )
        for EntryValue in Entries
    )


def DocumentFingerprint(Value: CadDocument) -> str:
    Parts = (
        repr(Value.configurations),
        repr(Value.parameters),
        repr(Value.support_planes),
        repr(Value.sketches),
        repr(Value.selections),
        repr(Value.feature_timeline),
        repr(Value.bodies),
        repr(Value.meshes),
        repr(Value.brep_payloads),
        repr(Value.units),
        repr(Value.assembly),
        repr(Value.brep),
        repr(Value.materials),
        repr(
            {
                KeyText: ItemValue
                for KeyText, ItemValue in Value.metadata.items()
                if KeyText not in {"creo.source_bytes", "creo.fingerprint"}
            }
        ),
    )
    return Sha256("\x1f".join(Parts).encode("utf-8")).hexdigest()


def ReadDocument(
    Source: KSourceType, Options: ReadOptions | None = None
) -> CadDocument:
    Settings = Options or ReadOptions()
    DataValue, Label = SourceBytes(Source)
    HeaderValue = ReadHeader(DataValue)
    TocValue = ReadToc(DataValue, HeaderValue.base, Strict=Settings.strict)
    Thumb = ReadThumb(DataValue, TocValue.entries)
    Payloads = ThumbPayload(Thumb)
    SectionRows = SectionTable(TocValue.entries)
    SectionNames = tuple(RowValue[0] for RowValue in SectionRows)
    UnitValue, UnitToken = ReadLengthUnit(DataValue, TocValue.entries)
    SectionFailures = ValidateSections(DataValue, TocValue.entries)
    if Settings.strict and SectionFailures:
        raise CreoFormat(
            "Creo section validation failed: " + "; ".join(SectionFailures)
        )
    Requested = Settings.configuration
    if Requested not in (None, KDefaultConfiguration, "creo:default"):
        raise CreoFormat(
            f"Creo part exposes only the default configuration, not {Requested!r}"
        )
    Notes = tuple(
        Diagnostic("creo.toc_note", NoteText, severity=Severity.KInfo)
        for NoteText in TocValue.notes
    )
    UnitNotes: tuple[Diagnostic, ...] = ()
    if UnitValue is None:
        UnitNotes = (
            Diagnostic(
                "creo.unit_unknown",
                f"The active length unit {UnitToken!r} is not decoded; the neutral unit field keeps its default and must not be trusted.",
                severity=Severity.KWarning,
            ),
        )
    Diagnostics = (
        *Notes,
        *UnitNotes,
        Diagnostic(
            "creo.container_only",
            "The PSB container, section directory, native thumbnail, and source bytes are decoded. Native geometry, sketches, dimensions, and feature records remain encoded, so no neutral feature or body is claimed.",
            severity=Severity.KWarning,
        ),
    )
    Metadata = FreezeMapping(
        {
            "adapter": KFormatId,
            "creo.base": HeaderValue.base,
            "creo.common_name": HeaderValue.common_name,
            "creo.feature_history_decoded": False,
            "creo.geometry_decoded": False,
            "creo.header_lines": HeaderValue.header_lines,
            "creo.kind": HeaderValue.kind,
            "creo.model_name": HeaderValue.model_name,
            "creo.product_version": HeaderValue.product_version,
            "creo.section_count": len(SectionRows),
            "creo.section_names": SectionNames,
            "creo.section_table": SectionRows,
            "creo.source_bytes": DataValue,
            "creo.source_sha256": Sha256(DataValue).hexdigest(),
            "creo.thumbnail_present": Thumb is not None,
            "creo.unit_token": UnitToken,
            "creo.version_line": HeaderValue.version_line,
        }
    )
    Value = CadDocument(
        source=CadSource(
            KFormatId,
            Label,
            Sha256(DataValue).hexdigest(),
            container_version="PSB",
            application_version=HeaderValue.product_version,
            attributes=FreezeMapping(
                {
                    "kind": HeaderValue.kind,
                    "model_name": HeaderValue.model_name,
                    "section_count": len(SectionRows),
                }
            ),
        ),
        configurations=(
            Configuration("creo:default", KDefaultConfiguration, active=True),
        ),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep_payloads=Payloads,
        diagnostics=Diagnostics,
        capabilities=frozenset(
            {Capability.KRoundtripMeta}
            | ({Capability.KNativePayloads} if Payloads else set())
        ),
        metadata=Metadata,
        units=UnitValue or UnitSystem.KMillimeter,
    )
    Value = Replace(
        Value,
        metadata=FreezeMapping(
            {**Metadata, "creo.fingerprint": DocumentFingerprint(Value)}
        ),
    )
    Value.assert_valid()
    return Value
