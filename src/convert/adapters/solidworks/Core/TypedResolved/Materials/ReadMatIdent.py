from re import fullmatch as MatchText

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatText import (
    ReadMatText,
)
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import KHatchClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatSlots import (
    CheckMatSlots,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# both independently serialized visual owners must carry the same material identity and hatch state
def ReadMatIdent(
    PartGraph: ConfigGraph, ManagerValue: CmgrGraph, ConfigValue: ArchiveNode
) -> tuple[str, str, int]:
    PartFields = PartGraph.RootValue.FieldsValue
    ConfigFields = ConfigValue.FieldsValue
    PartVisual = RequireNative(PartFields.get("f78"), "moVisualProperties_c")
    CfgVisual = RequireNative(ConfigFields.get("f78"), "moVisualProperties_c")
    PartHatch = RequireNative(PartFields.get("f1418"), KHatchClass.NameValue)
    CfgHatch = RequireNative(ConfigFields.get("fc48"), KHatchClass.NameValue)
    CheckMatSlots(PartGraph.MapValue, PartVisual, PartHatch)
    CheckMatSlots(ManagerValue.MapValue, CfgVisual, CfgHatch)
    PartMat = NativeRecord(PartVisual.FieldsValue.get("f20"))
    ConfigMat = NativeRecord(CfgVisual.FieldsValue.get("f20"))
    IdentText = ReadMatText(ConfigMat.get("f20"))
    ModeFields = ("f70", "has80", "has90", "has98")
    ModesValue = tuple(ConfigMat.get(NameValue) for NameValue in ModeFields)
    if (
        ReadMatText(PartMat.get("f20")) != IdentText
        or PartHatch.FieldsValue != CfgHatch.FieldsValue
        or ModesValue != tuple(PartMat.get(NameValue) for NameValue in ModeFields)
        or ModesValue not in ((0, 0, 1, 0), (0, 1, 1, 0))
    ):
        raise BodyUnsupported(
            "SOLIDWORKS assigned material visual owners disagree or use an unqualified layout"
        )
    MatchValue = MatchText(r"([^|]+)\|([^|]+)\|(0|[1-9][0-9]{0,9})", IdentText)
    if (
        MatchValue is None
        or not IdentText.isprintable()
        or int(MatchValue[3]) > 0x7FFFFFFF
    ):
        raise BodyUnsupported(
            "SOLIDWORKS assigned material requires a named catalog and explicit native id"
        )
    return MatchValue[1], MatchValue[2], int(MatchValue[3])
