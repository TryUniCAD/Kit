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


# radial displays use their actual radius or diameter style and retain its line mode
def ReadRadialStyle(
    ModelValue: ArchiveNode, IsDiameter: bool
) -> tuple[LinearStyle, bool]:
    if ModelValue.ClassValue != RuntimeClass("moPart_c", 1):
        raise ValueError("radial style requires its actual part model")
    Details = FieldRecord(FieldRecord(ModelValue.FieldsValue.get("fae0")).get("f13b0"))
    Subtype = FieldRecord(Details.get("f960" if IsDiameter else "f3f8"))
    if FieldInt(Subtype, "f44") != 0 or FieldInt(Details, "fd8") & 2:
        raise ValueError(
            "radial display requires zero tolerance and freely placed text"
        )
    IsSolid = not (
        FieldInt(Subtype, "f104") & 2 if IsDiameter else FieldInt(Subtype, "f100") & 4
    )
    return ProjectDimStyle(Details, Subtype), IsSolid
