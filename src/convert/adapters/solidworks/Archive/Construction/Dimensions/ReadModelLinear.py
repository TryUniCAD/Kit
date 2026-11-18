from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ProjectDimStyle import (
    ProjectDimStyle,
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
    return ProjectDimStyle(Details, StyleValue)
