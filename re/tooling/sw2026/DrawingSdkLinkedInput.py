from __future__ import annotations

from DrawingSdkInput import blank_input, checked_fields
from SdkBlindPartSettings import settings
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawInput import LinkedDrawInput
from convert.adapters.solidworks.Drawing.Construction.Supports.ViewNames import ViewNames
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.serialization.Deserialize import FromData


def part_settings(job):
    part = checked_fields(job["part"], ("document", "settings"))
    values = checked_fields(part["settings"], ("styles", "document_units", "analysis_units", "system", "target", "provenance", "definition", "output", "hatch_name", "manager_name", "density_kg_m3", "design_intent", "selected_leader"))
    checked_fields(values["styles"], ("standard", "font_name", "line_style_name", "language_id", "print_widths_m", "exclusion_names", "task_labels", "cutlist_expressions"))
    for name in ("document_units", "analysis_units"):
        checked_fields(values[name], ("length_unit", "angle_unit", "unit_system", "decimal_places"))
    checked_fields(values["system"], ("folders", "planes", "cabinet_name", "origin_name", "origin_axis", "created_at", "construction_flag"))
    checked_fields(values["system"]["planes"], ("x", "y", "z"))
    checked_fields(values["target"], ("date_code", "parasolid_version"))
    checked_fields(values["provenance"], ("author", "company", "comment", "created_at", "modified_at", "updated_at", "originating_build_code", "license_origin", "cjk_saved"))
    checked_fields(values["definition"], ("drafting_standard", "detail_flags", "tessellation", "system_preference_7a", "journal_name"))
    checked_fields(values["output"], ("path_name", "saved_at"))
    return settings(values)


def linked_input(job):
    checked_fields(job, ("schema", "drawing_document", "native", "part", "support_names"))
    drawing = FromData(job["drawing_document"])
    if type(drawing) is not DrawingData or len(drawing.Sheets) != 1:
        raise ValueError("linked SDK job requires a real serialized single-sheet neutral drawing")
    native = checked_fields(job["native"], ("options", "provenance", "ui", "output"))
    sheet = drawing.Sheets[0]
    bare = {"schema": "kit.sw2026.sdk-blank-drawing-process.v1", **native,
            "drawing": {"ActiveSheetId": drawing.ActiveSheetId,
                        "Sheets": [{"EntityId": sheet.EntityId, "EntityName": sheet.EntityName,
                                    "SheetWidth": sheet.SheetWidth, "SheetHeight": sheet.SheetHeight,
                                    "ScaleRatio": list(sheet.ScaleRatio)}]}}
    base = blank_input(bare)
    names = checked_fields(job["support_names"], ("detail", "sheet_plane", "sheet_profile", "model_plane", "model_profile"))
    return LinkedDrawInput(drawing, base.OptionsValue, base.UiSettings, base.HeaderValue, base.FileValue, base.HistoryValue,
                           ViewNames(names["detail"], names["sheet_plane"], names["sheet_profile"], names["model_plane"], names["model_profile"]))
