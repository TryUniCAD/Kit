from copy import deepcopy as CopyValue
from typing import cast as CastValue


# whole process rejections must mutate real neutral intent and typed provenance without replacing the construction algorithm
def BlankRejects(JobValue: dict[str, object]) -> dict[str, dict[str, object]]:
    RefsValue = [
        {
            "EntityId": "child",
            "SourcePath": "C:\\neutral\\child.SLDPRT",
            "SourceFormatId": "solidworks.sldprt",
        }
    ]
    ViewsValue = [
        {
            "EntityId": "view",
            "EntityName": "front",
            "ModelRefId": "child",
            "ConfigurationName": "Primary",
            "PositionValue": {"x": 0.1, "y": 0.1},
            "OrientationName": "*Front",
            "ScaleRatio": [1.0, 1.0],
        }
    ]
    SheetValues = CastValue(
        list[object], CastValue(dict[str, object], JobValue["drawing"])["Sheets"]
    )
    ChangesValue: tuple[tuple[str, str, object], ...] = (
        ("active", "drawing/ActiveSheetId", "other"),
        ("sheet_id", "drawing/Sheets/0/EntityId", 41),
        ("no_sheets", "drawing/Sheets", []),
        ("many_sheets", "drawing/Sheets", SheetValues * 2),
        ("paper_width", "drawing/Sheets/0/SheetWidth", 0.3),
        ("paper_height", "drawing/Sheets/0/SheetHeight", 0.2),
        ("sheet_views", "drawing/Sheets/0/Views", ViewsValue),
        ("model_refs", "drawing/ModelRefs", RefsValue),
        ("unknown_content", "drawing/Annotations", ["unrepresented"]),
        ("scale_fraction", "drawing/Sheets/0/ScaleRatio", [1.5, 1.0]),
        ("scale_boolean", "drawing/Sheets/0/ScaleRatio", [True, 1.0]),
        ("scale_zero", "drawing/Sheets/0/ScaleRatio", [0.0, 1.0]),
        ("scale_range", "drawing/Sheets/0/ScaleRatio", [1000000, 1]),
        ("sheet_separator", "drawing/Sheets/0/EntityName", "invalid@sheet"),
        ("xml_control", "options/property_view", "invalid\x01"),
        (
            "block_version",
            "options/block_identity",
            "00000000-0000-1000-8000-000000000000",
        ),
        ("block_invalid", "options/block_identity", "invalid"),
        ("epochs", "options/created_at", 1794871232),
        ("auto_link", "options/auto_dim_text_link", 1),
        ("service_pack", "options/target/service_pack", 4),
        ("xml_name", "options/name", "invalid\x01"),
        ("history_native", "provenance/originating_build_code", 0x80000000),
        ("cjk_provenance", "provenance/language_id", 1041),
        ("time_order", "provenance/modified_at", 1794871200),
        ("path_suffix", "output/path_name", "C:\\neutral\\invalid.SLDPRT"),
        ("relative_path", "output/path_name", "invalid.SLDDRW"),
        ("save_order", "output/saved_at", 1794871200),
        ("ui_standard", "ui/drafting_standard", "moUnknown_c"),
        ("ui_tessellation", "ui/tessellation", [True, 15, 3, False]),
        ("ui_display", "ui/detail_flags", [64]),
        ("ui_journal", "ui/journal_name", ""),
    )
    ResultsValue: dict[str, dict[str, object]] = {}
    for Label, PathValue, Replacement in ChangesValue:
        FreshJob = CopyValue(JobValue)
        FocusValue: dict[str, object] | list[object] = FreshJob
        KeysValue = str(PathValue).split("/")
        for KeyValue in KeysValue[:-1]:
            if isinstance(FocusValue, dict):
                FocusValue = CastValue(
                    dict[str, object] | list[object], FocusValue[KeyValue]
                )
            else:
                FocusValue = CastValue(
                    dict[str, object] | list[object], FocusValue[int(KeyValue)]
                )
        if isinstance(FocusValue, dict):
            FocusValue[KeysValue[-1]] = Replacement
        else:
            FocusValue[int(KeysValue[-1])] = Replacement
        ResultsValue[str(Label)] = FreshJob
    return ResultsValue
