from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    MakeAnnoView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# explicit activity and shown assignments use a registered view or its reserved unassigned identity
def SelectAnnoId(ViewIds: dict[str | None, int], NameValue: str | None) -> int:
    if (
        type(NameValue) is not str and NameValue is not None
    ) or NameValue not in ViewIds:
        raise ValueError("annotation membership names no registered view")
    return ViewIds[NameValue]


# the ordinary part installs its validated ordered annotation catalog and view memberships together
def PutAnnoCatalog(
    ModelValue: ArchiveNode,
    Version: int,
    InputValues: tuple[AnnoViewInput, ...],
    ActiveName: str | None,
    ShownNames: tuple[str | None, ...],
) -> dict[str, ArchiveNode]:
    Fields = RequireNode(ModelValue, "moPart_c").FieldsValue
    Catalog = RequireNode(Fields.get("fa48"), "suObList").FieldsValue
    if (
        Version != 19000
        or Fields.get("fb4") != 0
        or Catalog.get("n") != 0
        or Catalog.get("items")
        or Fields.get("feb0") != KNoAnno
        or Fields.get("feb4") != KNoAnno
        or Fields.get("nec8") != 0
        or Fields.get("fec0")
    ):
        raise ValueError(
            "annotation registration requires the empty ordinary part catalog"
        )
    if not 1 <= len(InputValues) <= 3:
        raise ValueError(
            "expected an ordered bounded catalog and explicit shown view roles"
        )
    Views: dict[str, ArchiveNode] = {}
    for Intent in InputValues:
        ViewValue = MakeAnnoView(Intent, KNoAnno + len(Views) + 1)
        if Intent.NameValue in Views:
            raise ValueError("ambiguous authored annotation view names")
        Views[Intent.NameValue] = ViewValue
    ViewIds: dict[str | None, int] = {
        NameValue: FieldInt(Value.FieldsValue, "f360")
        for NameValue, Value in Views.items()
    }
    ViewIds[None] = KNoAnno
    ShownIds = tuple(SelectAnnoId(ViewIds, NameValue) for NameValue in ShownNames)
    if len(ShownIds) != len(set(ShownIds)):
        raise ValueError("ambiguous shown annotation membership")
    ActiveId = SelectAnnoId(ViewIds, ActiveName)
    Catalog.update(n=len(Views), items=tuple({"o": Value} for Value in Views.values()))
    Fields.update(
        feb0=KNoAnno + len(Views),
        feb4=ActiveId,
        nec8=len(ShownIds),
        fec0=tuple({"v": ViewId} for ViewId in sorted(ShownIds)),
    )
    return Views
