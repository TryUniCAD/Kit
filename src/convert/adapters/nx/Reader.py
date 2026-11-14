from __future__ import annotations as Annotations
from dataclasses import replace as Replace
import hashlib as Hashlib
from pathlib import Path as FilePath
import re as RegexLib
from typing import cast as CastValue
import xml.etree.ElementTree as XmlTree  # noqa: DUO107

from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams
from convert.adapters.nx.Format import KInfoValue
from convert.adapters.nx.Payload import NxPayload
from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams
from convert.geometry.Parasolid import DecodeBrepMut
from interchange import (
    Body as BodyRecord,
    BrepModel,
    BrepPayload,
    CadDocument as CadDoc,
    CadSource,
    Configuration as Config,
    Diagnostic as DiagnosticInfo,
    FeatureKind,
    FeatureStep,
    NativeFeatureDefinition,
    PayloadRole,
    Severity,
    TopologyCounts,
    UnitSystem,
    frozen_mapping as FrozenMapping,
    infer_capabilities as InferCapabilities,
)

# the nx format id remains stable across reader writer and registry discovery
KFormatId = KInfoValue.format_id

# the native document payload id anchors exact source stream replay
KNativeDocId = "nx:native-document"

# the native feature id anchors the retained object model graph
KNativeFeatureId = "nx:native-feature"

# the native document payload keeps the complete source container for replay
KNativeDocKind = "native-document"

# the parasolid payload kind identifies inflated geometry streams
KParasolidKind = "partition"

# the nx part suffix is the only accepted source extension
KPartSuffix = ".prt"

# the build string pattern recovers the application version from native bytes
KBuildPattern = RegexLib.compile(rb"NX\s+\d{4}\.\d+")


# source bytes are read once so probing and parsing observe identical input
def ReadSource(Source: KSourceType) -> tuple[bytes, str]:
    if isinstance(Source, (bytes, bytearray)):
        return (bytes(Source), "<memory>")
    if isinstance(Source, (str, FilePath)):
        PathValue = FilePath(Source).expanduser().resolve()
        return (PathValue.read_bytes(), str(PathValue))
    Reader = getattr(Source, "read", None)
    if not callable(Reader):
        raise TypeError("NX source must be a path, bytes, or binary stream")
    Value = Reader()
    if not isinstance(Value, (bytes, bytearray)):
        raise TypeError("NX source stream must be binary")
    return (bytes(Value), getattr(Source, "name", "<stream>"))


# probing recognizes both modern and compound nx containers without decoding
def ProbeNx(Source: KSourceType) -> ProbeResult:
    try:
        DataValue, _ = ReadSource(Source)
        if DataValue.startswith(b"SPLMSSTR"):
            _ = ReadSplm(DataValue)
            return ProbeResult(KFormatId, 1.0, "SPLMSSTR native NX container")
        if DataValue.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
            Compound = ReadCompound(DataValue)
            Paths = {Stream.path for Stream in ReadStreams(Compound)}
            if any(PathValue.endswith("UG_PART/UG_PART") for PathValue in Paths):
                return ProbeResult(KFormatId, 1.0, "compound NX container")
        return ProbeResult(KFormatId, 0.0, "not an NX part container")
    except (OSError, TypeError, ValueError) as ErrorInfo:
        return ProbeResult(KFormatId, 0.0, str(ErrorInfo))


# reading projects native geometry and retains the exact source document
def ReadNx(Source: KSourceType, Options: ReadOptions | None = None) -> CadDoc:
    Settings = Options or ReadOptions()
    DataValue, Label = ReadSource(Source)
    ContainerData = OpenContainer(DataValue)
    Streams = ContainerData[1]
    ContainerName = ContainerData[2]
    PartData = Streams.get("UG_PART/UG_PART")
    if PartData is None:
        PartData = Streams.get("/Root/UG_PART/UG_PART")
    if PartData is None:
        raise ValueError("NX part has no UG_PART payload")
    Payload = ReadPayload(PartData)
    Attributes = ParseAttributes(Streams)
    References = ParseReferences(Streams)
    Geometry = DecodeGeometry(Payload, Settings)
    BrepValue = Geometry[0]
    Payloads = Geometry[2]
    Feature = MakeNativeStep(Payload, PartData)
    BodyRecords = MakeBodies(BrepValue, Feature.id)
    if BrepValue is not None:
        BrepValue = Replace(
            BrepValue,
            bodies=tuple(
                Replace(BodyValue, design_body_id=BodyRecords[Index].id)
                for Index, BodyValue in enumerate(BrepValue.bodies)
            ),
        )
    NativePayload = BrepPayload(
        KNativeDocId,
        KFormatId,
        KNativeDocKind,
        ContainerName,
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream="UG_PART/UG_PART",
        role=PayloadRole.KDocument,
        file_extension=KPartSuffix,
        attributes=FrozenMapping(
            {
                "container": ContainerName,
                "stream_count": len(Streams),
                "segment_count": len(Payload.rows),
                "section_count": len(Payload.sections),
            }
        ),
    )
    Version = GetBuildVersion(PartData)
    MetaValue = {
        "nx.container": ContainerName,
        "nx.streams": tuple(
            (NameValue, len(Value)) for NameValue, Value in Streams.items()
        ),
        "nx.segment_count": len(Payload.rows),
        "nx.om_section_count": len(Payload.sections),
        "nx.parasolid_stream_count": sum(
            (Stream.kind == "parasolid" for Stream in Payload.streams)
        ),
        "nx.section_markers": Payload.SectionMarkers(),
        "nx.attributes": Attributes,
        "nx.external_references": References,
        "nx.application_version": Version,
    }
    DocValue = CadDoc(
        source=CadSource(
            KFormatId,
            Label,
            Hashlib.sha256(DataValue).hexdigest(),
            container_version=ContainerName,
            application_version=Version,
        ),
        configurations=(Config("nx:default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(Feature,),
        bodies=BodyRecords,
        brep_payloads=(NativePayload, *Payloads),
        brep=BrepValue,
        diagnostics=(
            DiagnosticInfo(
                "nx.native_object_model_retained",
                "The NX object model and Parasolid streams are retained exactly; feature parameters are not projected into neutral parameters.",
                Severity.WARNING,
                entity_id=Feature.id,
            ),
        ),
        capabilities=frozenset(),
        metadata=FrozenMapping(MetaValue),
        units=UnitSystem.KMillimeter,
    )
    DocValue = Replace(
        DocValue,
        capabilities=InferCapabilities(DocValue, RoundtripMeta=True),
    )
    if Settings.strict:
        DocValue.assert_valid()
    return DocValue


# container opening normalizes both nx envelopes into one stream map
def OpenContainer(DataValue: bytes) -> tuple[object, dict[str, bytes], str]:
    if DataValue.startswith(b"SPLMSSTR"):
        SplmValue = ReadSplm(DataValue)
        Streams = {
            PathValue.removeprefix("/Root/"): Value
            for PathValue, Value in SplmStreams(SplmValue)
        }
        return (SplmValue, Streams, "SPLMSSTR")
    Compound = ReadCompound(DataValue)
    Streams = {Stream.path: Stream.data for Stream in ReadStreams(Compound)}
    return (Compound, Streams, "compound")


# attributes are bounded xml and only string values enter document metadata
def ParseAttributes(Streams: dict[str, bytes]) -> dict[str, str]:
    DataValue = Streams.get("part/attrs") or Streams.get("/Root/part/attrs")
    if not DataValue:
        return {}
    try:
        RootValue = XmlTree.fromstring(DataValue)
    except XmlTree.ParseError:
        return {}
    Output: dict[str, str] = {}
    for Element in RootValue.iter("Attribute"):
        Title = Element.get("utf8title") or Element.get("title")
        Value = Element.get("utf8value") or Element.get("value")
        if Title and Value is not None:
            Output[Title] = Value
    return Output


# external references are recovered from the native extref string table
def ParseReferences(Streams: dict[str, bytes]) -> tuple[str, ...]:
    Output: list[str] = []
    for NameValue, DataValue in Streams.items():
        if "ExternalReferences" not in NameValue:
            continue
        for Match in RegexLib.finditer(rb"[ -~]{4,512}\.prt", DataValue):
            try:
                TextValue = Match.group().decode("utf-8")
            except UnicodeDecodeError:
                continue
            if TextValue not in Output:
                Output.append(TextValue)
    return tuple(Output)


# geometry decoding uses the existing parasolid reader at the stream boundary
def DecodeGeometry(
    Payload: NxPayload, Settings: ReadOptions
) -> tuple[BrepModel | None, tuple[BodyRecord, ...], tuple[BrepPayload, ...]]:
    if not Settings.include_brep:
        return (None, (), ())
    Models: list[BrepModel] = []
    Payloads: list[BrepPayload] = []
    for Index, Stream in enumerate(Payload.streams):
        if Stream.kind != "parasolid":
            continue
        try:
            ModelValue = DecodeBrepMut(Stream.inflated)
        except (TypeError, ValueError):
            continue
        if ModelValue is None:
            continue
        Models.append(ModelValue)
        Payloads.append(
            BrepPayload(
                f"nx:parasolid:{Index}",
                "parasolid",
                KParasolidKind,
                ModelValue.schema_version,
                Hashlib.sha256(Stream.inflated).hexdigest(),
                data=Stream.inflated,
                source_stream=f"UG_PART:{Stream.offset}",
                role=PayloadRole.KBrep,
                file_extension=".x_b",
            )
        )
    if not Models:
        return (None, (), tuple(Payloads))
    return (Models[0], (), tuple(Payloads))


# native feature records retain the object model without inventing parameters
def MakeNativeStep(Payload: NxPayload, PartData: bytes) -> FeatureStep:
    return FeatureStep(
        id=KNativeFeatureId,
        name="NX native feature graph",
        kind=FeatureKind.KNative,
        order=0,
        definition=NativeFeatureDefinition(
            format_id=KFormatId,
            type_id="UG_PART",
            object_data=FrozenMapping(
                {
                    "part_sha256": Hashlib.sha256(PartData).hexdigest(),
                    "segment_count": len(Payload.rows),
                    "section_count": len(Payload.sections),
                    "section_markers": Payload.SectionMarkers(),
                }
            ),
        ),
        attributes=FrozenMapping(
            {
                "native_payload_id": KNativeDocId,
                "native_feature_graph": True,
            }
        ),
    )


# body records connect decoded topology to the retained native feature
def MakeBodies(ModelValue: BrepModel | None, FeatureId: str) -> tuple[BodyRecord, ...]:
    if ModelValue is None:
        return ()
    Output: list[BodyRecord] = []
    for Index, BodyValue in enumerate(ModelValue.bodies):
        Counts = CountBody(ModelValue, BodyValue)
        Output.append(
            BodyRecord(
                id=f"nx:body:{Index + 1}",
                name=f"Body {Index + 1}",
                final_feature_id=FeatureId,
                topology=Counts,
                attributes=FrozenMapping(
                    {
                        "native_body_id": BodyValue.id,
                        "native_region_count": len(BodyValue.region_ids),
                    }
                ),
            )
        )
    return tuple(Output)


# topology counts follow region shell face links without geometric evaluation
def CountBody(ModelValue: BrepModel, BodyValue: object) -> TopologyCounts:
    RegionIds = CastValue(tuple[str, ...], getattr(BodyValue, "region_ids", ()))
    Regions = {Value.id: Value for Value in ModelValue.regions}
    ShellUses = {Value.id: Value for Value in ModelValue.shell_uses}
    Shells = {Value.id: Value for Value in ModelValue.shells}
    FaceUses = {Value.id: Value for Value in ModelValue.face_uses}
    Faces = {Value.id: Value for Value in ModelValue.faces}
    FaceIds: set[str] = set()
    ShellIds: set[str] = set()
    for RegionId in RegionIds:
        Region = Regions.get(RegionId)
        if Region is None:
            continue
        for ShellUseId in Region.shell_use_ids:
            ShellUse = ShellUses.get(ShellUseId)
            if ShellUse is None:
                continue
            Shell = Shells.get(ShellUse.shell_id)
            if Shell is None:
                continue
            ShellIds.add(Shell.id)
            for FaceUseId in Shell.face_use_ids:
                FaceUse = FaceUses.get(FaceUseId)
                if FaceUse is not None and FaceUse.face_id in Faces:
                    FaceIds.add(FaceUse.face_id)
    return TopologyCounts(
        solid_count=1 if RegionIds else 0,
        shell_count=len(ShellIds),
        face_count=len(FaceIds),
        edge_count=len(ModelValue.edges),
        vertex_count=len(ModelValue.vertices),
    )


# application version extraction keeps source provenance useful without guessing
def GetBuildVersion(PartData: bytes) -> str:
    Match = KBuildPattern.search(PartData)
    return Match.group().decode("ascii") if Match else ""
