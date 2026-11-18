from __future__ import annotations

from uuid import UUID

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings
from convert.adapters.solidworks.Drawing.Construction.Model.DrawFolders import DrawFolders
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import BlankDrawInput
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import DrawDocOptions
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.geometry.Models.VectorPlane import PlaneVector


def checked_fields(value, required, optional=()):
    if type(value) is not dict or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError("neutral drawing job fields differ from the complete declared input schema")
    return value


def neutral_sheet(row):
    checked_fields(row, ("EntityId", "EntityName", "SheetWidth", "SheetHeight", "ScaleRatio"), ("Views",))
    views = []
    for value in row.get("Views", ()):
        checked_fields(value, ("EntityId", "EntityName", "ModelRefId", "ConfigurationName", "PositionValue"),
                       ("OrientationName", "ScaleRatio", "ModelToSheet", "OutlineValues"))
        position = checked_fields(value["PositionValue"], ("x", "y"))
        views.append(DrawingView(value["EntityId"], value["EntityName"], value["ModelRefId"], value["ConfigurationName"],
                                 PlaneVector(position["x"], position["y"]), value.get("OrientationName"),
                                 None if value.get("ScaleRatio") is None else tuple(value["ScaleRatio"]),
                                 None if value.get("ModelToSheet") is None else tuple(value["ModelToSheet"]),
                                 None if value.get("OutlineValues") is None else tuple(value["OutlineValues"])))
    return DrawingSheet(row["EntityId"], row["EntityName"], row["SheetWidth"], row["SheetHeight"], tuple(row["ScaleRatio"]), tuple(views))


def blank_input(job):
    checked_fields(job, ("schema", "drawing", "options", "provenance", "ui", "output"))
    data, options, provenance, ui = (job[key] for key in ("drawing", "options", "provenance", "ui"))
    checked_fields(data, ("ActiveSheetId", "Sheets"), ("ModelRefs",))
    checked_fields(options, ("name", "property_view", "sheet_names", "folder_names", "styles", "units", "target", "created_at", "block_identity", "auto_dim_text_link"))
    checked_fields(provenance, ("author", "company", "comment", "created_at", "modified_at", "updated_at", "originating_build_code", "license_origin", "language_id", "cjk_saved"))
    checked_fields(ui, ("drafting_standard", "detail_flags", "tessellation", "system_preference_7a", "journal_name"))
    checked_fields(job["output"], ("path_name", "saved_at"))
    refs = tuple(DrawingModelRef(**checked_fields(row, ("EntityId", "SourcePath", "SourceFormatId"))) for row in data.get("ModelRefs", ()))
    drawing = DrawingData(data["ActiveSheetId"], tuple(neutral_sheet(row) for row in data["Sheets"]), refs)
    folders, names, styles, units, target = (options[key] for key in ("folder_names", "sheet_names", "styles", "units", "target"))
    checked_fields(folders, ("annotations", "binder", "comments", "blocks", "ink_markups", "review_markups"))
    checked_fields(names, ("plane_name", "profile_name", "detail_name"))
    checked_fields(styles, ("standard", "font_name", "line_style_name", "language_id", "print_widths_m", "exclusion_names", "task_labels", "cutlist_expressions"))
    checked_fields(units, ("length_unit", "angle_unit", "unit_system", "decimal_places"))
    checked_fields(target, ("date_code", "parasolid_version"))
    native = DrawDocOptions(
        options["name"], options["property_view"], SheetNames(names["plane_name"], names["profile_name"], names["detail_name"]),
        DrawFolders(folders["annotations"], folders["binder"], folders["comments"], folders["blocks"], folders["ink_markups"], folders["review_markups"]),
        StyleInput(styles["standard"], styles["font_name"], styles["line_style_name"], styles["language_id"],
                   tuple(styles["print_widths_m"]), tuple(styles["exclusion_names"]), tuple(styles["task_labels"]), tuple(styles["cutlist_expressions"])),
        UnitInput(units["length_unit"], units["angle_unit"], units["unit_system"], units["decimal_places"]),
        FeatureTarget(target["date_code"], target["parasolid_version"], 19000, 5, 2),
        options["created_at"], UUID(options["block_identity"]), options["auto_dim_text_link"],
    )
    settings = ModelDefSettings(ui["drafting_standard"], tuple(ui["detail_flags"]), tuple(ui["tessellation"]),
                                ui["system_preference_7a"], ui["journal_name"], 19000)
    header = HeaderInput(provenance["author"], provenance["company"], provenance["comment"], provenance["created_at"],
                         provenance["modified_at"], provenance["updated_at"])
    history = HistoryInput(provenance["created_at"], provenance["comment"], provenance["originating_build_code"],
                           provenance["license_origin"], provenance["language_id"], provenance["cjk_saved"])
    return BlankDrawInput(drawing, native, settings, header,
                          SelfFileInput(job["output"]["path_name"], job["output"]["saved_at"]), history)
