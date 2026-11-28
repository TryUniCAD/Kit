from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# display memberships refer to actual registered annotation views independently of model cameras
def ReadAnnoView(ModelValue: ArchiveNode, NameValue: str) -> ArchiveNode:
    ModelFields = RequireNode(ModelValue, "moPart_c").FieldsValue
    Catalog = RequireNode(ModelFields.get("fa48"), "suObList").FieldsValue
    Views = tuple(
        RequireNode(RowValue.get("o"), "moAnnotationView_c")
        for RowValue in ReadRows(Catalog.get("items"))
    )
    ViewIds = tuple(FieldInt(Value.FieldsValue, "f360") for Value in Views)
    if (
        not ViewIds
        or Catalog.get("n") != len(Views)
        or len(ViewIds) != len(set(ViewIds))
        or min(ViewIds) <= KNoAnno
        or max(ViewIds) != ModelFields.get("feb0")
    ):
        raise ValueError("angular display cannot join an invalid annotation catalog")
    Matches = tuple(
        Value for Value in Views if Value.FieldsValue.get("f358") == NameValue
    )
    if type(NameValue) is not str or len(Matches) != 1:
        raise ValueError("angular display requires one actual authored annotation view")
    return Matches[0]
