from collections.abc import Mapping

from convert.Geometry.Parasolid import EncodePartData
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSweepXmt import (
    EncodeSweepXmt,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeSwSheet import MakeSwSheet
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireRecord,
)
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# alternate sweep options and solved body caches are outside the measured cold definition
def CheckColdSweep(FieldsValue: Mapping[str, object]) -> None:
    if any(
        FieldsValue[NameValue]
        for NameValue in (
            "f270",
            "f274",
            "f278",
            "f2ac",
            "f2b0",
            "f7c",
            "f80",
            "f230",
            "f78",
            "f234",
            "f238",
            "f240",
            "f248",
            "f2b4",
            "f280",
            "f288",
            "f290",
            "f27c",
            "f2a8",
            "f258",
            "f260",
            "f298",
            "f2a0",
            "f2b8",
            "f3b0",
        )
    ):
        raise BodyUnsupported(
            "unsupported option or saved result in cold SOLIDWORKS standard sweep"
        )
    if (
        FieldsValue["f70"] != 1.0
        or FieldsValue["f24c"] != 1
        or any(
            ReadRows(RequireRecord(FieldsValue[NameValue])["items"])
            for NameValue in ("f300", "f98", "fe0", "f320", "f340")
        )
    ):
        raise BodyUnsupported(
            "unsupported alternate section or equation in cold SOLIDWORKS standard sweep"
        )


# embedded section serialization recomputes the sheet and compressed length from its typed authored circle
def WriteSwSectMut(FrameValue: WriteFrame) -> None:
    FieldsValue = FrameValue.ScopeValue.FieldsValue
    CircleValue = FieldsValue.get("CircleValue")
    if (
        FrameValue.NodeValue.ClassValue != RuntimeClass("moGeneralCurveRef_w", 1)
        or FrameValue.NodeValue.FieldsValue.get("has_fc8") != 1
        or set(FieldsValue) != {"CircleValue"}
        or type(CircleValue) is not CircleGeometry
    ):
        raise BodyUnsupported("sweep section requires an actual typed circle owner")
    BodyValue = EncodePartData(EncodeSweepXmt(MakeSwSheet(CircleValue), False))
    OutputValue = FrameValue.WriterValue.OutputValue
    OutputValue.extend(EncodeScalar(0, "u8"))
    OutputValue.extend(EncodeScalar(len(BodyValue) + 1, "i32"))
    OutputValue.extend(EncodeScalar(0, "u8"))
    OutputValue.extend(BodyValue)
    FrameValue.WriterValue.ContextValue.UsageValue.SchemaCalls[
        "sweep.embeddedSection19000"
    ] += 1


# only this concrete local schema writer handles the sweep section transport
def WriteSwSchema(FrameValue: WriteFrame, SchemaName: str) -> None:
    if SchemaName == "sweep.embeddedSection19000":
        WriteSwSectMut(FrameValue)
        return
    if SchemaName == "sweep.data19000":
        CheckColdSweep(FrameValue.ScopeValue.FieldsValue)
    WriteSchemaMut(FrameValue, SchemaName)


# one sweep must emit its two picked profiles and one newly generated embedded sheet
def CheckSweepUse(ContextValue: BodyContext) -> None:
    CallsValue = ContextValue.UsageValue.SchemaCalls
    if any(
        CallsValue[NameValue] != CountValue
        for NameValue, CountValue in (
            ("moSweep_c", 1),
            ("moGeneralCurveRef_w", 2),
            ("moCompProfile_c", 2),
            ("moWireContact_c", 1),
            ("sweep.data19000", 1),
            ("sweep.embeddedSection19000", 1),
        )
    ):
        raise BodyUnsupported(
            "cold standard sweep must emit one body feature and its actual section and path"
        )
