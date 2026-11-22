from struct import pack as PackValues

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import (
    ReadModelLinear,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# both local displays use their own text and leader modes with the actual default model style
def MakeChmfView(
    Feature: ArchiveNode,
    Handle: ArchiveNode,
    ViewId: int,
    Driver: float,
    Angular: bool,
) -> dict[str, object]:
    Fields = MakeCommonView(Handle, False, -3 if Angular else -2, 13 if Angular else 18)
    Style = ReadModelLinear(ArchiveNode.RequireNode(Feature.FieldsValue["owner"]))
    Fields.update(Style.ProjectionValue)
    Fields.update(
        owner=Feature,
        f2b0=({"v": ViewId},),
        n2b0=1,
        f8a4=(FieldInt(Fields, "f8a4") & ~0x50) | Style.UnderText,
        fb64=(FieldInt(Fields, "fb64") & ~0x103000) | Style.FlagValue,
        f5b0={**RequireRecord(Fields["f5b0"]), "data": PackValues("<d", Driver)},
    )
    return Fields
