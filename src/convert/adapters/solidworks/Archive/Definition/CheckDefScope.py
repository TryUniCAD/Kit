from collections.abc import Mapping

from convert.adapters.base.ContractCompat import IsObjectDict
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Definition.CheckAsmDef import CheckAsmDef
from convert.adapters.solidworks.Archive.Definition.CheckDefRender import CheckDefRender


# the ordinary definition cannot represent optional sketch scene ole or variation owners
def CheckDefScope(FieldsValue: Mapping[str, object], *, Assembly: bool = False) -> None:
    KindValue = "assembly" if Assembly else "part"
    if FieldsValue.get("fa74") != 1 or FieldsValue.get("fac8") != 0:
        raise BodyUnsupported(
            f"SOLIDWORKS {KindValue} Definition has an alternate UI prefix"
        )
    if (
        not Assembly
        and ReadStyleNum(FieldsValue.get("f1688"), "SOLIDWORKS part density", 0.0) <= 0
    ):
        raise ValueError("SOLIDWORKS part density must be positive")
    if (
        any(
            FieldsValue.get(FieldName) is not None
            for FieldName in ("fac0", "fb20", "fa10", "f12e8")
        )
        or FieldsValue.get("f11a0") != []
    ):
        raise BodyUnsupported(
            f"SOLIDWORKS {KindValue} Definition has optional UI objects"
        )
    ModelData = FieldsValue.get("fbf0")
    BaseValue = FieldsValue.get("basedoc")
    OleValue = BaseValue.get("ole") if IsObjectDict(BaseValue) else None
    if (
        not IsObjectDict(ModelData)
        or ModelData.get("f08") is not None
        or not IsObjectDict(OleValue)
        or OleValue.get("f7f8") != []
    ):
        raise BodyUnsupported(
            f"SOLIDWORKS {KindValue} Definition has an alternate scene or OLE owner"
        )
    CheckDefRender(FieldsValue, Assembly=Assembly)
    if Assembly:
        CheckAsmDef(FieldsValue)
