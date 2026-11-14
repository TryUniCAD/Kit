from __future__ import annotations

from hashlib import sha256 as HashValue
import os as OsModule
from pathlib import Path as FilePath
from types import MappingProxyType

from interchange.document.models.DocumentCaps import InferCaps
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Severity
from interchange.records.RecordDiagnostic import Diagnostic

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.creo.CreoFormat import CreoFormat
from convert.adapters.creo.Fingerprint import GetFingerprint
from convert.adapters.creo.Format import KFormatId
from convert.adapters.creo.Header import ReadHeader
from convert.adapters.creo.Toc import ReadToc


def IsCreoPath(Target: KTargetType) -> bool:
    if not isinstance(Target, (str, FilePath)):
        Writer = getattr(Target, "write", None)
        return callable(Writer) and getattr(Target, "encoding", None) is None
    NameText = FilePath(Target).name.casefold()
    return NameText.endswith(".prt") or ".prt." in NameText


def NativeBytes(Value: CadDocument) -> tuple[bytes, str]:
    DataValue = Value.metadata.get("creo.source_bytes")
    Expected = Value.metadata.get("creo.source_sha256")
    Fingerprint = Value.metadata.get("creo.fingerprint")
    if (
        not isinstance(DataValue, bytes)
        or not isinstance(Expected, str)
        or not isinstance(Fingerprint, str)
    ):
        raise CreoFormat(
            "Creo writing requires a source-preserved Creo document; independent PSB synthesis is not implemented"
        )
    if not DataValue.startswith(b"#UGC:"):
        raise CreoFormat("retained Creo source bytes are not a PSB document")
    HeaderValue = ReadHeader(DataValue)
    _ = ReadToc(DataValue, HeaderValue.base, Strict=False)
    Actual = HashValue(DataValue).hexdigest()
    if Actual != Expected:
        raise CreoFormat("retained Creo source bytes changed after reading")
    if GetFingerprint(Value) != Fingerprint:
        raise CreoFormat(
            "Creo document was edited after reading; exact source replay cannot encode the edit"
        )
    return (DataValue, HeaderValue.kind)


def WriteBytes(
    Target: KTargetType, DataValue: bytes, Overwrite: bool
) -> FilePath | None:
    if not isinstance(Target, (str, FilePath)):
        Writer = getattr(Target, "write", None)
        if not callable(Writer):
            raise TypeError("Creo destination must be a path or binary stream")
        Written = Writer(DataValue)
        if Written is not None and Written != len(DataValue):
            raise OSError("short Creo stream write")
        return None
    PathValue = FilePath(Target).expanduser().resolve()
    if PathValue.exists() and not Overwrite:
        raise FileExistsError(PathValue)
    PathValue.parent.mkdir(parents=True, exist_ok=True)
    Temporary = PathValue.with_name(PathValue.name + f".{OsModule.getpid()}.tmp")
    try:
        with Temporary.open("xb") as Handle:
            _ = Handle.write(DataValue)
            Handle.flush()
            OsModule.fsync(Handle.fileno())
        OsModule.replace(Temporary, PathValue)
    except BaseException:
        try:
            Temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return PathValue


def WriteDocument(
    DocumentValue: CadDocument,
    Target: KTargetType,
    Options: WriteOptions | None = None,
) -> WriteResult:
    Settings = Options or WriteOptions()
    if Settings.validate:
        DocumentValue.assert_valid()
    if Settings.destination_format not in (None, KFormatId, "prt"):
        raise ValueError("unsupported Creo destination format")
    if not IsCreoPath(Target):
        raise ValueError("Creo destination must end in .prt")
    DataValue, _ = NativeBytes(DocumentValue)
    OutputValue = WriteBytes(Target, DataValue, Settings.overwrite)
    Capabilities = tuple(
        sorted(GetDocumentCaps(DocumentValue), key=lambda Value: Value.value)
    )
    Transfers = tuple(
        CapTransfer(CapabilityValue, TransferMode.KNative)
        for CapabilityValue in Capabilities
    )
    SectionValue = DocumentValue.metadata.get("creo.section_count", 0)
    SectionCount = SectionValue if isinstance(SectionValue, int) else 0
    Metadata = MappingProxyType(
        {
            "application_usable": False,
            "compatibility": "native-exact-source-replay",
            "container": "PSB",
            "mode": "exact_native_roundtrip",
            "native_geometry": True,
            "native_history": True,
            "native_self_contained": True,
            "referenced_files_written": 0,
            "section_count": SectionCount,
            "vendor_loadable": False,
        }
    )
    Diagnostics = (
        *DocumentValue.diagnostics,
        Diagnostic(
            "creo.source_replay_only",
            "The output is byte-identical to the retained Creo source. Independent PSB synthesis, geometry regeneration, and native feature authoring are not implemented.",
            severity=Severity.KWarning,
        ),
    )
    return WriteResult(
        OutputValue,
        KFormatId,
        len(DataValue),
        diagnostics=Diagnostics,
        metadata=Metadata,
        transfers=Transfers,
        requirements=(),
        application_usable=False,
        vendor_loadable=False,
    )
