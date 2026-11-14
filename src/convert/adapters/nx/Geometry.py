from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass
import hashlib as Hashlib

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.nx.Payload import NxPayload
from convert.geometry.Parasolid import DecodeBrepMut
from interchange import (
    BrepModel,
    BrepPayload,
    Diagnostic as DiagnosticInfo,
    PayloadRole,
    Severity,
)

# the parasolid payload kind identifies inflated geometry streams
KParasolidKind = "partition"


# decoded geometry keeps models payloads and omissions visible in one result
@DataClass(frozen=True, slots=True)
class NxGeometry:
    brep: BrepModel | None
    payloads: tuple[BrepPayload, ...]
    diagnostics: tuple[DiagnosticInfo, ...]


# geometry decoding uses the existing parasolid reader at the stream boundary
def ReadGeometry(Payload: NxPayload, Settings: ReadOptions) -> NxGeometry:
    if not Settings.include_brep:
        return NxGeometry(None, (), ())
    Models: list[BrepModel] = []
    Payloads: list[BrepPayload] = []
    Diagnostics: list[DiagnosticInfo] = []
    for Index, Stream in enumerate(Payload.streams):
        if Stream.kind != "parasolid":
            continue
        ModelValue = TryDecode(Stream.inflated)
        if ModelValue is None:
            Diagnostics.append(Undecoded(Stream.offset))
            continue
        Models.append(ModelValue)
        Payloads.append(
            MakeBrepPayload(Index, Stream.offset, Stream.inflated, ModelValue)
        )
    return ResolveModels(Models, Payloads, Diagnostics, Settings)


# one stream decode keeps malformed geometry separate from unsupported schema
def TryDecode(DataValue: bytes) -> BrepModel | None:
    try:
        return DecodeBrepMut(DataValue)
    except (TypeError, ValueError):
        return None


# stream payloads retain wrapper provenance and decoded schema version
def MakeBrepPayload(
    Index: int, Offset: int, DataValue: bytes, ModelValue: BrepModel
) -> BrepPayload:
    return BrepPayload(
        f"nx:parasolid:{Index}",
        "parasolid",
        KParasolidKind,
        ModelValue.schema_version,
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream=f"UG_PART:{Offset}",
        role=PayloadRole.KBrep,
        file_extension=".x_b",
    )


# several decodable streams cannot be merged without a native body map
def ResolveModels(
    Models: list[BrepModel],
    Payloads: list[BrepPayload],
    Diagnostics: list[DiagnosticInfo],
    Settings: ReadOptions,
) -> NxGeometry:
    if not Models:
        if Settings.strict and Diagnostics:
            raise ValueError("NX part has undecodable Parasolid geometry")
        return NxGeometry(None, tuple(Payloads), tuple(Diagnostics))
    if len(Models) == 1:
        return NxGeometry(Models[0], tuple(Payloads), tuple(Diagnostics))
    AllDiagnostics = (
        *Diagnostics,
        DiagnosticInfo(
            "nx.multiple_parasolid_streams",
            "The NX part contains several Parasolid streams; only the first is projected.",
            Severity.WARNING,
        ),
    )
    if Settings.strict:
        raise ValueError("multiple NX Parasolid body streams are not merged")
    return NxGeometry(Models[0], tuple(Payloads), AllDiagnostics)


# one diagnostic names the exact stream so callers can inspect it directly
def Undecoded(Offset: int) -> DiagnosticInfo:
    return DiagnosticInfo(
        "nx.parasolid_stream_undecoded",
        f"The NX Parasolid stream at offset {Offset} was not decoded; geometry is omitted.",
        Severity.WARNING,
    )
