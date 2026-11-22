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
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwFrame import (
    KSwFrameLimit,
    ReadSwFrame,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwSect import ReadSwSect
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Resolved.Sweeps.WriteSwSchema import (
    CheckColdSweep,
)


# the stored section owns one finite right circle on a canonical standalone kernel sheet
def ReadSwSheetMut(FrameValue: ReadFrame) -> None:
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
    CircleValue = ReadSwSect(NodesValue, RequireXmt(NodesValue, 1, 12), Embedded=True)
    FrameValue.ScopeValue.FieldsValue["CircleValue"] = CircleValue
    FrameValue.ContextValue.UsageValue.SchemaCalls["sweep.embeddedSection19000"] += 1


# section decoding remains isolated to explicitly selected current sweep sections
def ReadSwSchema(FrameValue: ReadFrame, SchemaName: str) -> None:
    if SchemaName == "sweep.embeddedSection19000":
        ReadSwSheetMut(FrameValue)
        return
    ReadSchemaMut(FrameValue, SchemaName)
    if SchemaName == "sweep.data19000":
        CheckColdSweep(FrameValue.ScopeValue.FieldsValue, SavedResult=True)
