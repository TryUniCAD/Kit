from ansi_style.Codec import plain
from SpatialTextMut import concrete, require
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import (
    ReadNamedDef,
)


def fields(child_bytes, drawing_bytes, orientation, mode):
    child_archive = SldprtArchive.from_bytes(child_bytes)
    drawing_archive = SldprtArchive.from_bytes(drawing_bytes)
    child = ReadNativeLink(child_archive, 0)
    ui = ReadModelDef(child_archive.require("Contents/Definition"), 19000)
    require(
        WriteModelDef(ui.GraphValue).OutputValue
        == child_archive.require("Contents/Definition"),
        "complete child Definition did not replay exactly",
    )
    drawing = ReadNamedDef(
        drawing_archive.require("Contents/Definition"), 19000, orientation
    )
    wanted = "moANSI_c" if mode == "ansi" else "moISO_c"
    records = {}
    for label, root in (
        ("child", ui.GraphValue.DocumentValue),
        ("drawing", drawing.GraphValue.DocumentValue),
    ):
        standard = concrete(root.FieldsValue["fba8"], wanted)
        require(not standard.FieldsValue, "UI drafting-standard body is not empty")
        records[label + "_ui"] = {
            "class": standard.ClassValue.NameValue,
            "schema": standard.ClassValue.SchemaValue,
            "fields": {},
        }
    model = concrete(
        drawing.GraphValue.DocumentValue.FieldsValue["model"], "moDrawing_c"
    )
    records["child_details"] = plain(child.ConfigValue.RootValue.FieldsValue["fae0"])
    records["drawing_details"] = plain(model.FieldsValue["fae0"])
    for label in ("child_details", "drawing_details"):
        require(
            records[label]["f10"] == (0 if mode == "ansi" else 1)
            and records[label]["f138"] == 1,
            "actual detail selector or constructor ownership differs",
        )
    return child, drawing, records
