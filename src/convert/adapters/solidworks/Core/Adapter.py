from __future__ import annotations

from convert.adapters.base import ProbeResult, Source
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry
from convert.adapters.solidworks.Container.Format import (
    KDrawingFormatId as KDrawingFormatId,
)
from convert.adapters.solidworks.Core.NativeSourceKey import (
    KSourceFormatKey as KSourceFormatKey,
)
from convert.adapters.solidworks.Core.Properties.WithPartProps import (
    WithPartProps as WithPartProps,
)
from convert.adapters.solidworks.Core.Reading import ReadAdapter as ReadModule
from convert.adapters.solidworks.Core.Reading.ReadAdapter import (
    ApplyNative as ApplyNative,
    ArcEllipseGeometry as ArcEllipseGeometry,
    ArcGeometry as ArcGeometry,
    ArcParabolaGeometry as ArcParabolaGeometry,
    AsmInstanceId as AsmInstanceId,
    BooleanOperation as BooleanOperation,
    BrepPayloads as BrepPayloads,
    BytesIO as BytesIO,
    CadDocument as CadDocument,
    CircleGeometry as CircleGeometry,
    Companion as Companion,
    ComponentDocument as ComponentDocument,
    Configurations as Configurations,
    ConstraintReference as ConstraintReference,
    Diagnostic as Diagnostic,
    EllipseGeometry as EllipseGeometry,
    GeometryKind as GeometryKind,
    InfoAction as InfoAction,
    KAsmFormatId,
    KFormatId,
    KPartBodyId as KPartBodyId,
    KSourceBytesKey as KSourceBytesKey,
    KSourceKeys as KSourceKeys,
    KSourceSemanticShaTwoFive as KSourceSemanticShaTwoFive,
    KSourceShaTwoFiveSixKey as KSourceShaTwoFiveSixKey,
    LineGeometry as LineGeometry,
    MateConstraint as MateConstraint,
    MateGroups as MateGroups,
    MateInstance as MateInstance,
    MatePayload as MatePayload,
    NativeAssembly as NativeAssembly,
    NativeAssemblyDefinition as NativeAssemblyDefinition,
    NativeAssemblyOccurrence as NativeAssemblyOccurrence,
    NativeGeometry as NativeGeometry,
    NativePartModel as NativePartModel,
    NeutralMateKinA as NeutralMateKinA,
    PairProtocol,
    Parameter as Parameter,
    ParameterRole as ParameterRole,
    ParameterValue as ParameterValue,
    PathValue as PathValue,
    PlaneId as PlaneId,
    PointGeometry as PointGeometry,
    Probe,
    ReadAction as ReadAction,
    ReadNativePart as ReadNativePart,
    ReadSldprt as ReadSldprt,
    ReferencePlaneFeature as ReferencePlaneFeature,
    SelectionPathElement as SelectionPathElement,
    SemanticShaTwo as SemanticShaTwo,
    SketchConstraint as SketchConstraint,
    SplineGeometry as SplineGeometry,
    SldprtReader,
)
from interchange import CadDocument as CadDoc


# the compatibility facade retains its established imports when the reader moves
__all__ = (
    "annotations",
    "ProbeResult",
    "Source",
    "KTargetType",
    "WriteOptions",
    "WriteResult",
    "AdapterRegistry",
    "KDrawingFormatId",
    "KSourceFormatKey",
    "WithPartProps",
    "ReadModule",
    "ApplyNative",
    "ArcEllipseGeometry",
    "ArcGeometry",
    "ArcParabolaGeometry",
    "AsmInstanceId",
    "BooleanOperation",
    "BrepPayloads",
    "BytesIO",
    "CadDocument",
    "CircleGeometry",
    "Companion",
    "ComponentDocument",
    "Configurations",
    "ConstraintReference",
    "Diagnostic",
    "EllipseGeometry",
    "GeometryKind",
    "InfoAction",
    "KAsmFormatId",
    "KFormatId",
    "KPartBodyId",
    "KSourceBytesKey",
    "KSourceKeys",
    "KSourceSemanticShaTwoFive",
    "KSourceShaTwoFiveSixKey",
    "LineGeometry",
    "MateConstraint",
    "MateGroups",
    "MateInstance",
    "MatePayload",
    "NativeAssembly",
    "NativeAssemblyDefinition",
    "NativeAssemblyOccurrence",
    "NativeGeometry",
    "NativePartModel",
    "NeutralMateKinA",
    "PairProtocol",
    "Parameter",
    "ParameterRole",
    "ParameterValue",
    "PathValue",
    "PlaneId",
    "PointGeometry",
    "Probe",
    "ReadAction",
    "ReadNativePart",
    "ReadSldprt",
    "ReferencePlaneFeature",
    "SelectionPathElement",
    "SemanticShaTwo",
    "SketchConstraint",
    "SplineGeometry",
    "SldprtReader",
    "CadDoc",
    "SldprtAdapter",
    "COMPONENT_TREE_STREAM",
    "CONTAINER_VERSIONS",
    "CONTENT_TYPES_STREAM",
    "DIRECTION_AXIS_ROLE",
    "DISPLAY_LISTS_STREAM",
    "FORMAT_ID_BY_SUFFIX",
    "INFO",
    "KEYWORDS_STREAM",
    "KIT_DOCUMENT_STREAM",
    "KIT_RESOLVED_STREAM",
    "MATES_STREAM_NAME",
    "MATES_STREAM_SUFFIX",
    "MATE_VALUE_SEMANTICS",
    "NATIVE_MATE_ALIGNMENT_BY_CODE",
    "NATIVE_MATE_ENTITY_MARKERS",
    "NATIVE_MATE_NEUTRAL_KIND_ALIASES",
    "PLANE_FEATURE_TYPES",
    "Path",
    "RELATIONSHIPS_STREAM",
    "RESOLVED_FEATURES_STREAM",
    "SOLID_BODY_FEATURE_TYPES",
    "SUFFIX_BY_FORMAT_ID",
    "build_sldprt",
    "contains_parasolid_payload",
    "dataclass",
    "decode_brep_model",
    "decode_mate_list",
    "decode_native_assembly",
    "decode_native_model",
    "decode_partition_stream",
    "defaultdict",
    "encode_blank_partition_stream",
    "encode_brep_model",
    "encode_partition_stream",
    "filter_document",
    "frozen_mapping",
    "hashlib",
    "infer_capabilities",
    "is_binary_destination",
    "is_native_parasolid_payload",
    "json",
    "math",
    "operation_axis_subelement",
    "os",
    "re",
    "read_sldprt",
    "replace",
    "retained_capabilities",
    "semantic_metadata",
    "source_payload_indexes",
    "struct",
    "suppress",
    "tempfile",
    "with_wrapper_metadata",
    "DecodeNativeModel",
)


# direct adapter callers keep the same reader and the canonical checked writer
class SldprtAdapter(SldprtReader, PairProtocol):
    __slots__ = ()

    # source assessment stays non destructive because probing precedes any conversion commitment
    def probe(self, SourceValue: Source) -> ProbeResult:
        return Probe(self, SourceValue)

    # direct adapter callers use the canonical selection and checked output transaction
    def write(
        self,
        document: CadDoc,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        FormatId = (
            options.destination_format if isinstance(options, WriteOptions) else None
        )
        if FormatId is None:
            if document.DrawingValue is not None:
                FormatId = KDrawingFormatId
            elif document.assembly is not None:
                FormatId = KAsmFormatId
            else:
                FormatId = KFormatId
        from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

        RegistryValue = AdapterRegistry()
        RegistryValue.RegisterWriter(SldprtWriter())
        return RegistryValue.WriteDocument(
            document, destination, FormatId=FormatId, OptionsData=options
        )


# this binding exists because shared behavior needs one stable value
COMPONENT_TREE_STREAM = ReadModule.COMPONENT_TREE_STREAM

# this binding exists because shared behavior needs one stable value
CONTAINER_VERSIONS = ReadModule.CONTAINER_VERSIONS

# this binding exists because shared behavior needs one stable value
CONTENT_TYPES_STREAM = ReadModule.CONTENT_TYPES_STREAM

# this binding exists because shared behavior needs one stable value
DIRECTION_AXIS_ROLE = ReadModule.DIRECTION_AXIS_ROLE

# this binding exists because shared behavior needs one stable value
DISPLAY_LISTS_STREAM = ReadModule.DISPLAY_LISTS_STREAM

# this binding exists because shared behavior needs one stable value
FORMAT_ID_BY_SUFFIX = ReadModule.FORMAT_ID_BY_SUFFIX

# this binding exists because shared behavior needs one stable value
INFO = ReadModule.INFO

# this binding exists because shared behavior needs one stable value
KEYWORDS_STREAM = ReadModule.KEYWORDS_STREAM

# this binding exists because shared behavior needs one stable value
KIT_DOCUMENT_STREAM = ReadModule.KIT_DOCUMENT_STREAM

# this binding exists because shared behavior needs one stable value
KIT_RESOLVED_STREAM = ReadModule.KIT_RESOLVED_STREAM

# this binding exists because shared behavior needs one stable value
MATES_STREAM_NAME = ReadModule.MATES_STREAM_NAME

# this binding exists because shared behavior needs one stable value
MATES_STREAM_SUFFIX = ReadModule.MATES_STREAM_SUFFIX

# this binding exists because shared behavior needs one stable value
MATE_VALUE_SEMANTICS = ReadModule.MATE_VALUE_SEMANTICS

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ALIGNMENT_BY_CODE = ReadModule.NATIVE_MATE_ALIGNMENT_BY_CODE

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_MARKERS = ReadModule.NATIVE_MATE_ENTITY_MARKERS

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_NEUTRAL_KIND_ALIASES = ReadModule.NATIVE_MATE_NEUTRAL_KIND_ALIASES

# this binding exists because shared behavior needs one stable value
PLANE_FEATURE_TYPES = ReadModule.PLANE_FEATURE_TYPES

# this binding exists because shared behavior needs one stable value
Path = ReadModule.Path

# this binding exists because shared behavior needs one stable value
RELATIONSHIPS_STREAM = ReadModule.RELATIONSHIPS_STREAM

# this binding exists because shared behavior needs one stable value
RESOLVED_FEATURES_STREAM = ReadModule.RESOLVED_FEATURES_STREAM

# this binding exists because shared behavior needs one stable value
SOLID_BODY_FEATURE_TYPES = ReadModule.SOLID_BODY_FEATURE_TYPES

# this binding exists because shared behavior needs one stable value
SUFFIX_BY_FORMAT_ID = ReadModule.SUFFIX_BY_FORMAT_ID

# this binding exists because shared behavior needs one stable value
annotations = ReadModule.annotations

# this binding exists because shared behavior needs one stable value
build_sldprt = ReadModule.build_sldprt

# this binding exists because shared behavior needs one stable value
contains_parasolid_payload = ReadModule.contains_parasolid_payload

# this binding exists because shared behavior needs one stable value
dataclass = ReadModule.dataclass

# this binding exists because shared behavior needs one stable value
decode_brep_model = ReadModule.decode_brep_model

# this binding exists because shared behavior needs one stable value
decode_mate_list = ReadModule.decode_mate_list

# this binding exists because shared behavior needs one stable value
decode_native_assembly = ReadModule.decode_native_assembly

# this binding exists because shared behavior needs one stable value
decode_native_model = ReadModule.decode_native_model

# this binding exists because shared behavior needs one stable value
decode_partition_stream = ReadModule.decode_partition_stream

# this binding exists because shared behavior needs one stable value
defaultdict = ReadModule.defaultdict

# this binding exists because shared behavior needs one stable value
encode_blank_partition_stream = ReadModule.encode_blank_partition_stream

# this binding exists because shared behavior needs one stable value
encode_brep_model = ReadModule.encode_brep_model

# this binding exists because shared behavior needs one stable value
encode_partition_stream = ReadModule.encode_partition_stream

# this binding exists because shared behavior needs one stable value
filter_document = ReadModule.filter_document

# this binding exists because shared behavior needs one stable value
frozen_mapping = ReadModule.frozen_mapping

# this binding exists because shared behavior needs one stable value
hashlib = ReadModule.hashlib

# this binding exists because shared behavior needs one stable value
infer_capabilities = ReadModule.infer_capabilities

# this binding exists because shared behavior needs one stable value
is_binary_destination = ReadModule.is_binary_destination

# this binding exists because shared behavior needs one stable value
is_native_parasolid_payload = ReadModule.is_native_parasolid_payload

# this binding exists because shared behavior needs one stable value
json = ReadModule.json

# this binding exists because shared behavior needs one stable value
math = ReadModule.math

# this binding exists because shared behavior needs one stable value
operation_axis_subelement = ReadModule.operation_axis_subelement

# this binding exists because shared behavior needs one stable value
os = ReadModule.os

# this binding exists because shared behavior needs one stable value
re = ReadModule.re

# this binding exists because shared behavior needs one stable value
read_sldprt = ReadModule.read_sldprt

# this binding exists because shared behavior needs one stable value
replace = ReadModule.replace

# this binding exists because shared behavior needs one stable value
retained_capabilities = ReadModule.retained_capabilities

# this binding exists because shared behavior needs one stable value
semantic_metadata = ReadModule.semantic_metadata

# this binding exists because shared behavior needs one stable value
source_payload_indexes = ReadModule.source_payload_indexes

# this binding exists because shared behavior needs one stable value
struct = ReadModule.struct

# this binding exists because shared behavior needs one stable value
suppress = ReadModule.suppress

# this binding exists because shared behavior needs one stable value
tempfile = ReadModule.tempfile

# this binding exists because shared behavior needs one stable value
with_wrapper_metadata = ReadModule.with_wrapper_metadata


# the native model decoder remains accessible through the established adapter import
DecodeNativeModel = ReadModule.decode_native_model
