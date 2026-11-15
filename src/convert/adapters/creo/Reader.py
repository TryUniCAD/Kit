from __future__ import annotations

from contextlib import suppress
from dataclasses import replace as Replace
from hashlib import sha256 as HashValue
from pathlib import Path as FilePath

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumDocument import Severity
from interchange.enums.EnumUnits import UnitSystem
from interchange.enums.EnumValues import ParameterRole
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureBody import DesignBody
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordParameter import ParameterValue
from interchange.records.RecordProvenance import Provenance
from interchange.records.RecordProvenance import ProvenanceSpan
from interchange.records.RecordSource import CadSource
from interchange.records.RecordTopology import TopologyCounts
from interchange.core.Common import FreezeMapping

from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.creo.Compress import KMaxSectionBytes
from convert.adapters.creo.CreoFormat import CreoFormat
from convert.adapters.creo.Fingerprint import GetFingerprint
from convert.adapters.creo.Format import KFormatId
from convert.adapters.creo.Header import ReadHeader
from convert.adapters.creo.Records import FeatureSteps
from convert.adapters.creo.Records import ReadFeatureRows
from convert.adapters.creo.Stream import ReadDimensions
from convert.adapters.creo.VisibGeom import ReadGeometry
from convert.adapters.creo.VisibGeom import ReadLogicalObjects
from convert.adapters.creo.VisibGeom import ReadMassProperties
from convert.adapters.creo.VisibGeom import ReadTopology
from convert.adapters.creo.Toc import CreoEntry
from convert.adapters.creo.Toc import ReadSection
from convert.adapters.creo.Toc import ReadToc

# the control part declares this configuration and we match it
KDefaultConfiguration = "Default"


# unit tokens appear as text so they are mapped once
KUnitByToken = {
    "mm": UnitSystem.KMillimeter,
    "m": UnitSystem.KMeter,
    "in": UnitSystem.KInch,
}


# probe and read both need bytes from several source shapes
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
        try:
            PositionValue: object = TellMethod()
        except (OSError, ValueError):
            PositionValue = None
        if isinstance(PositionValue, int):
            Position = PositionValue
    ValueData = Reader()
    if Position is not None and callable(SeekMethod):
        with suppress(OSError, ValueError):
            _ = SeekMethod(Position)
    if not isinstance(ValueData, (bytes, bytearray)):
        raise TypeError("Creo source stream must be binary")
    return (bytes(ValueData), str(getattr(Source, "name", "<stream>")))


# thumbnails are the only image data the interchange model keeps
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


# the model wants image payloads not the raw vendor block
def ThumbPayload(Thumb: bytes | None) -> tuple[BrepPayload, ...]:
    if Thumb is None or len(Thumb) > KMaxSectionBytes:
        return ()
    Value = BrepPayload(
        id="creo:thumbnail:1",
        format_id="jpeg",
        kind="thumbnail",
        schema="jpeg",
        sha256=HashValue(Thumb).hexdigest(),
        data=Thumb,
        source_stream="THMB_IMG_MAIN",
        role=PayloadRole.KAuxiliary,
        file_extension=".jpg",
    )
    return (Value,)


# length units decide how every dimension is scaled
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
        TailText = BodyData[Start + len(Marker) :]
        Token = TailText.split(b"\x00", 1)[0].decode("latin-1").strip()
        return (KUnitByToken.get(Token), Token)
    return (None, "")


# display sections are optional so they are named in one place
KDisplaySections = frozenset(
    {
        "AssMrgPrt",
        "CGFMappingTable",
        "CGFPersistTable",
        "ColorSchemeInfo",
        "ColorSchemeInfoNew",
        "DispDataColor",
        "DispDataTable",
        "FeatRefData",
        "IndentTag",
        "THMB_IMG_INDX",
        "THMB_IMG_MAIN",
    }
)


# callers want to know which sections were absent
def CheckSections(DataValue: bytes, Entries: tuple[CreoEntry, ...]) -> tuple[str, ...]:
    Failures: list[str] = []
    for EntryValue in Entries:
        if EntryValue.name in KDisplaySections:
            continue
        try:
            _ = ReadSection(DataValue, EntryValue)
        except CreoFormat as ErrorInfo:
            Failures.append(f"{EntryValue.name}: {ErrorInfo}")
    return tuple(Failures)


# the section table is queried repeatedly so it is built once
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


# this is the single entry point the adapter contract calls
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
    SectionFailures = CheckSections(DataValue, TocValue.entries)
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
    SectionNotes = tuple(
        Diagnostic("creo.section_invalid", Failure, severity=Severity.KWarning)
        for Failure in SectionFailures
    )
    FeatureRows = ()
    FeatureRecords = ()
    FeatureNotes: tuple[Diagnostic, ...] = ()
    FeatureEntry = next(
        (
            EntryValue
            for EntryValue in TocValue.entries
            if EntryValue.name == "AllFeatur"
        ),
        None,
    )
    if FeatureEntry is not None:
        try:
            FeatureRows = ReadFeatureRows(ReadSection(DataValue, FeatureEntry))
        except CreoFormat as ErrorInfo:
            FeatureNotes = (
                Diagnostic(
                    "creo.feature_rows_invalid",
                    f"The AllFeatur section could not be decoded: {ErrorInfo}",
                    severity=Severity.KWarning,
                ),
            )
        else:
            FeatureRecords = FeatureSteps(FeatureRows)
    DimensionRows = ()
    ParameterRecords: tuple[Parameter, ...] = ()
    DefinitionEntry = next(
        (
            EntryValue
            for EntryValue in TocValue.entries
            if EntryValue.name == "FeatDefs"
        ),
        None,
    )
    if DefinitionEntry is not None:
        try:
            DimensionRows = ReadDimensions(ReadSection(DataValue, DefinitionEntry))
        except CreoFormat as ErrorInfo:
            FeatureNotes = (
                *FeatureNotes,
                Diagnostic(
                    "creo.dimensions_invalid",
                    f"The FeatDefs section could not be decoded: {ErrorInfo}",
                    severity=Severity.KWarning,
                ),
            )
    ProtrusionIds = tuple(
        FeatureValue.id
        for FeatureValue in FeatureRecords
        if FeatureValue.attributes.get("creo.root_class") == 917
    )
    OwnerId = ProtrusionIds[0] if len(ProtrusionIds) == 1 else ""
    ParameterRecords = tuple(
        Parameter(
            id=f"creo:dimension:{IndexValue}",
            name=f"Creo dimension {IndexValue}",
            value=ParameterValue(Dimension.value, ValueKind.KNumber, UnitToken),
            role=ParameterRole.KDriving,
            owner_id=OwnerId,
            provenance=Provenance(
                KFormatId,
                str(Dimension.reference) if Dimension.reference is not None else "",
                spans=(
                    ProvenanceSpan(
                        "FeatDefs",
                        Dimension.offset,
                        Dimension.length,
                        "dimension_value",
                    ),
                ),
            ),
            attributes=FreezeMapping(
                {
                    "creo.dimension_reference": Dimension.reference,
                    "creo.dimension_index": IndexValue,
                }
            ),
        )
        for IndexValue, Dimension in enumerate(DimensionRows)
    )
    if OwnerId and ParameterRecords:
        ParameterIds = tuple(Value.id for Value in ParameterRecords)
        FeatureRecords = tuple(
            (
                Replace(FeatureValue, parameter_ids=ParameterIds)
                if FeatureValue.id == OwnerId
                else FeatureValue
            )
            for FeatureValue in FeatureRecords
        )
    SurfaceRows = ()
    CurveRows = ()
    LogicalObjects = ()
    GeometryEntry = next(
        (
            EntryValue
            for EntryValue in TocValue.entries
            if EntryValue.name == "VisibGeom"
        ),
        None,
    )
    if GeometryEntry is not None:
        try:
            GeometryData = ReadSection(DataValue, GeometryEntry)
            SurfaceRows, CurveRows = ReadGeometry(GeometryData)
            LogicalObjects = ReadLogicalObjects(GeometryData)
        except CreoFormat as ErrorInfo:
            FeatureNotes = (
                *FeatureNotes,
                Diagnostic(
                    "creo.geometry_invalid",
                    f"The VisibGeom section could not be decoded: {ErrorInfo}",
                    severity=Severity.KWarning,
                ),
            )
    TopologyValue = ReadTopology(CurveRows, len(SurfaceRows))
    MassValue = ReadMassProperties(SurfaceRows)
    BoundingValue = None
    if MassValue.minimum is not None and MassValue.maximum is not None:
        BoundingValue = BoundingBox(
            SpaceVector(*MassValue.minimum), SpaceVector(*MassValue.maximum)
        )
    BodyRecords: tuple[DesignBody, ...] = ()
    if SurfaceRows and FeatureRecords:
        FaceRecords = tuple(
            FreezeMapping(
                {
                    "id": f"creo:face:{Surface.geom_id}",
                    "geom_type": Surface.geom_type,
                    "feature_id": Surface.feature_id,
                    "envelope": Surface.envelope,
                    "outline": Surface.outline,
                    "local_system": Surface.local_system,
                }
            )
            for Surface in SurfaceRows
        )
        CurveRecords = tuple(
            FreezeMapping(
                {
                    "id": f"creo:curve:{Curve.curve_id}",
                    "curve_type": Curve.curve_type,
                    "feature_id": Curve.feature_id,
                    "points": Curve.points,
                }
            )
            for Curve in CurveRows
        )
        BodyRecords = (
            DesignBody(
                id="creo:body:1",
                name="Creo surface body",
                final_feature_id=FeatureRecords[-1].id,
                topology=TopologyCounts(
                    solid_count=TopologyValue.solid_count,
                    shell_count=TopologyValue.shell_count,
                    face_count=len(SurfaceRows),
                    edge_count=len(CurveRows),
                    vertex_count=MassValue.vertex_count,
                    volume=MassValue.volume,
                    bounding_box=BoundingValue,
                    valid=TopologyValue.valid,
                ),
                provenance=Provenance(
                    KFormatId,
                    "1",
                    spans=(
                        ProvenanceSpan(
                            "VisibGeom", 0, len(SurfaceRows), "surface_prototypes"
                        ),
                    ),
                ),
                attributes=FreezeMapping(
                    {
                        "creo.faces": FaceRecords,
                        "creo.curves": CurveRecords,
                        "creo.surface_count": len(SurfaceRows),
                        "creo.curve_count": len(CurveRows),
                        "creo.closed_loop_count": TopologyValue.closed_loop_count,
                        "creo.shell_count": TopologyValue.shell_count,
                        "creo.solid_count": TopologyValue.solid_count,
                        "creo.volume": MassValue.volume,
                        "creo.centroid": MassValue.centroid,
                        "creo.shell_closure_proven": TopologyValue.valid,
                        "creo.volume": MassValue.volume,
                        "creo.centroid": MassValue.centroid,
                        "creo.logical_object_count": len(LogicalObjects),
                        "creo.logical_objects": tuple(
                            FreezeMapping(
                                {
                                    "id": Logical.object_id,
                                    "type": Logical.object_type,
                                    "subtype": Logical.object_subtype,
                                    "feature_id": Logical.feature_id,
                                    "next_id": Logical.next_object_id,
                                }
                            )
                            for Logical in LogicalObjects
                        ),
                    }
                ),
            ),
        )
    Diagnostics = (
        *Notes,
        *UnitNotes,
        *SectionNotes,
        *FeatureNotes,
        Diagnostic(
            "creo.container_only",
            "The PSB container, section directory, native thumbnail, source bytes, AllFeatur feature identity rows, stored dimension values, and VisibGeom surface/curve prototypes are decoded. Shell closure is proven from the curve half-edge graph when every face loop closes and every edge is shared. Sketches and B-rep face geometry remain encoded.",
            severity=Severity.KWarning,
        ),
    )
    Metadata = FreezeMapping(
        {
            "adapter": KFormatId,
            "creo.base": HeaderValue.base,
            "creo.common_name": HeaderValue.common_name,
            "creo.closed_loop_count": TopologyValue.closed_loop_count,
            "creo.curve_count": len(CurveRows),
            "creo.logical_object_count": len(LogicalObjects),
            "creo.shell_count": TopologyValue.shell_count,
            "creo.shell_closure_proven": TopologyValue.valid,
            "creo.solid_count": TopologyValue.solid_count,
            "creo.volume": MassValue.volume,
            "creo.centroid": MassValue.centroid,
            "creo.dimension_count": len(DimensionRows),
            "creo.feature_history_decoded": False,
            "creo.feature_row_count": len(FeatureRows),
            "creo.feature_rows_decoded": bool(FeatureRows),
            "creo.geometry_decoded": TopologyValue.valid,
            "creo.surface_count": len(SurfaceRows),
            "creo.surface_prototypes_decoded": bool(SurfaceRows),
            "creo.header_lines": HeaderValue.header_lines,
            "creo.parameters_decoded": bool(ParameterRecords),
            "creo.kind": HeaderValue.kind,
            "creo.model_name": HeaderValue.model_name,
            "creo.product_version": HeaderValue.product_version,
            "creo.section_count": len(SectionRows),
            "creo.section_names": SectionNames,
            "creo.section_table": SectionRows,
            "creo.source_bytes": DataValue,
            "creo.source_sha256": HashValue(DataValue).hexdigest(),
            "creo.thumbnail_present": Thumb is not None,
            "creo.unit_token": UnitToken,
            "creo.version_line": HeaderValue.version_line,
        }
    )
    Value = CadDocument(
        source=CadSource(
            KFormatId,
            Label,
            HashValue(DataValue).hexdigest(),
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
        parameters=ParameterRecords,
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=FeatureRecords,
        bodies=BodyRecords,
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
        metadata=FreezeMapping({**Metadata, "creo.fingerprint": GetFingerprint(Value)}),
    )
    Value.assert_valid()
    return Value
