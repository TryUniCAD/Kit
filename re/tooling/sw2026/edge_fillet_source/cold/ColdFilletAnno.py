from dataclasses import dataclass

from FilletModel import require

from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import ReadAnnoBasis
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import PutAnnoCatalog
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import ReadAnnoView
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


@dataclass(frozen=True, slots=True)
class FilletAnnotations:
    views: tuple[AnnoViewInput, ...]
    driver_view: str
    active_view: str | None
    shown_views: tuple[str | None, ...]


def prepare_annotations(value: object) -> FilletAnnotations:
    require(type(value) is dict and set(value) == {"views", "driver_view", "active_view", "shown_views"},
            "expected explicit fillet annotation catalogue and view memberships")
    rows = value["views"]
    driver, active, shown = (value[name] for name in ("driver_view", "active_view", "shown_views"))
    require(type(rows) is list and 1 <= len(rows) <= 3
            and all(type(row) is dict and set(row) == {"name", "basis"} and type(row["name"]) is str
                    for row in rows)
            and type(driver) is str and bool(driver)
            and (active is None or type(active) is str) and type(shown) is list,
            "expected bounded fillet annotation views with an actual named driver view")
    views = tuple(AnnoViewInput(row["name"], ReadAnnoBasis(row["basis"])) for row in rows)
    require(any(view.NameValue == driver for view in views), "fillet driver view is absent from its catalogue")
    return FilletAnnotations(views, driver, active, tuple(shown))


def bind_annotations(model: ArchiveNode, display: ArchiveNode, version: int, intent: FilletAnnotations | None) -> None:
    if intent is None:
        return
    owners = PutAnnoCatalog(model, version, intent.views, intent.active_view, intent.shown_views)
    owner = ReadAnnoView(model, intent.driver_view)
    require(owner is owners[intent.driver_view], "fillet driver view differs from its allocated model owner")
    display.FieldsValue.update(n2b0=1, f2b0=({"v": owner.FieldsValue["f360"]},))


def read_annotation_binding(model: ArchiveNode, display: ArchiveNode) -> dict[str, str | int] | None:
    fields = display.FieldsValue
    rows = NativeRows(fields["f2b0"])
    require(fields["n2b0"] == len(rows) <= 1, "fillet requires at most one actual radial annotation membership")
    if not rows:
        return None
    (row,) = rows
    view_id = row["v"]
    catalog = RequireNative(model.FieldsValue["fa48"], "suObList")
    views = tuple(RequireNative(item["o"], "moAnnotationView_c") for item in NativeRows(catalog.FieldsValue["items"]))
    matches = tuple(view for view in views if view.FieldsValue["f360"] == view_id)
    require(len(matches) == 1, "fillet radius membership has no unique annotation view owner")
    (owner,) = matches
    name = owner.FieldsValue["f358"]
    require(type(name) is str and type(view_id) is int and ReadAnnoView(model, name) is owner,
            "fillet radius membership does not resolve in the actual model catalogue")
    return {"name": name, "id": view_id}
