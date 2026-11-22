from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalDescription,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSweepXmt import (
    EncodeSweepXmt,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeSwSheet import MakeSwSheet
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwFrame import (
    KSwFrameLimit,
    ReadSwFrame,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwSect import ReadSwSect
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Resolved.Sweeps.WriteSwSchema import (
    CheckColdSweep,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the stored section owns one finite right circle on a canonical standalone kernel sheet
def ReadSwSheetMut(FrameValue: ReadFrame, *, SavedResult: bool) -> None:
    if (
        FrameValue.NodeValue.ClassValue != RuntimeClass("moGeneralCurveRef_w", 1)
        or FrameValue.NodeValue.FieldsValue.get("has_fc8") != 1
    ):
        raise BodyUnsupported("SOLIDWORKS sweep section lacks its embedded owner")
    Cursor = FrameValue.ReaderValue.Cursor
    if Cursor.ReadUnsigned(1) != 0:
        raise BodyUnsupported("SOLIDWORKS sweep section must contain its kernel body")
    LengthValue = ReadScalarMut(Cursor, "i32")
    if type(LengthValue) is not int or not 1 < LengthValue <= min(
        KSwFrameLimit, Cursor.GetRemaining()
    ):
        raise BodyUnsupported("SOLIDWORKS sweep section has invalid kernel length")
    if Cursor.ReadUnsigned(1) != 0:
        raise BodyUnsupported("SOLIDWORKS sweep section has an alternate kernel flag")
    RawValue = ReadSwFrame(Cursor.TakeBytes(LengthValue - 1))
    NodesValue = ReadActiveNodes(
        RawValue, Description=KLocalDescription.decode("ascii")
    )
    if SavedResult:
        CircleValue = ReadSwSect(
            NodesValue, RequireXmt(NodesValue, 1, 12), Embedded=True
        )
    else:
        CircleValue = ReadColdSect(RawValue, NodesValue)
    FrameValue.ScopeValue.FieldsValue["CircleValue"] = CircleValue
    FrameValue.ContextValue.UsageValue.SchemaCalls["sweep.embeddedSection19000"] += 1


# cold publication still requires exact regeneration from its own neutral section
def ReadColdSect(RawValue: bytes, NodesValue: Mapping[int, XmtNode]) -> CircleGeometry:
    CurvesValue = tuple(
        NodeValue for NodeValue in NodesValue.values() if NodeValue.KindValue == 31
    )
    if len(CurvesValue) != 1:
        raise BodyUnsupported("SOLIDWORKS sweep section requires one circular carrier")
    RadiusValue = RequireScalar(CurvesValue[0].FieldsValue["radius"])
    CircleValue = CircleGeometry(PlaneVector(0.0, 0.0), RadiusValue)
    if RawValue != EncodeSweepXmt(MakeSwSheet(CircleValue), False):
        raise BodyUnsupported(
            "SOLIDWORKS sweep section differs from its typed Right sheet"
        )
    return CircleValue


# section decoding remains isolated to explicitly selected current sweep sections
def ReadSwSchema(
    FrameValue: ReadFrame, SchemaName: str, *, SavedResult: bool = False
) -> None:
    if SchemaName == "sweep.embeddedSection19000":
        ReadSwSheetMut(FrameValue, SavedResult=SavedResult)
        return
    ReadSchemaMut(FrameValue, SchemaName)
    if SchemaName == "sweep.data19000":
        CheckColdSweep(FrameValue.ScopeValue.FieldsValue, SavedResult=SavedResult)
