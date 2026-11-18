from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.StyleInteger import (
    StyleInteger,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# part and assembly linear displays must project the same actual document style while excluding unrelated or unresolved model owners
def ReadModelLinear(ModelValue: ArchiveNode) -> LinearStyle:
    if ModelValue.ClassValue not in (
        RuntimeClass("moPart_c", 1),
        RuntimeClass("moAssembly_c", 1),
    ):
        raise ValueError(
            "linear display requires a concrete current part or assembly style owner"
        )
    Details = FieldRecord(FieldRecord(ModelValue.FieldsValue.get("fae0")).get("f13b0"))
    StyleValue = FieldRecord(Details.get("fe0"))
    if FieldInt(StyleValue, "f44") != 0 or FieldInt(Details, "fd8") & 2:
        raise ValueError(
            "planar distance display requires zero tolerance and freely placed text"
        )
    UnitMode = StyleInteger(Details, "f6c", HighBound=0xFFFF)
    Projection: dict[str, object] = {
        "f870": UnitMode,
        "f874": UnitMode,
        "fb68": StyleInteger(StyleValue, "fc", HighBound=0xFFFF),
        "fb6c": StyleInteger(StyleValue, "f10", HighBound=0xFFFF),
        "f8ec": StyleInteger(StyleValue, "f84", HighBound=0xFFFF),
        "ff00": StyleInteger(Details, "fc0", LowBound=-(1 << 31)),
        "ff10": int(bool(FieldInt(StyleValue, "fe0") & 0x10000)),
        "fe40": StyleInteger(StyleValue, "f08"),
        "f30c": dict(FieldRecord(FieldRecord(StyleValue.get("fd0")).get("f10"))),
        "f320": dict(FieldRecord(FieldRecord(StyleValue.get("fd8")).get("f10"))),
    }
    UnderText = (
        0x40 if FieldInt(Details, "f74") == 0 and FieldInt(Details, "f60") == 0 else 0
    )
    FlagValue = FieldInt(Details, "fd8") & 0x100000
    FlagValue |= 0x1000 if FieldInt(StyleValue, "f78") else 0
    FlagValue |= 0x2000 if FieldInt(StyleValue, "f9c") else 0
    return LinearStyle(Projection, UnderText, FlagValue)
