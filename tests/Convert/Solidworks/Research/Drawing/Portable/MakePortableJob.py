from typing import cast as CastValue


# the sdk process must receive actual portable sheet intent and independently authored native presentation provenance
def MakePortableJob(Request: dict[str, object]) -> dict[str, object]:
    SheetValue = CastValue(dict[str, object], Request["sheet"])
    Provenance = CastValue(dict[str, object], Request["provenance"])
    Presentation = CastValue(dict[str, object], Request["presentation"])
    SheetId = "neutral:sheet:" + str(Request["name"])
    return {
        "schema": "kit.sw2026.sdk-blank-drawing-process.v1",
        "drawing": {
            "ActiveSheetId": SheetId,
            "Sheets": [
                {
                    "EntityId": SheetId,
                    "EntityName": SheetValue["name"],
                    "SheetWidth": 11 * 0.0254,
                    "SheetHeight": 8.5 * 0.0254,
                    "ScaleRatio": [
                        SheetValue["scale_numerator"],
                        SheetValue["scale_denominator"],
                    ],
                }
            ],
        },
        "options": {
            "name": Request["name"],
            "property_view": SheetValue["custom_property_view"],
            "sheet_names": Request["sheet_names"],
            "folder_names": Request["folder_names"],
            "styles": Presentation["styles"],
            "units": Presentation["units"],
            "target": Request["target"],
            "created_at": Provenance["created_at"],
            "block_identity": Provenance["block_identity"],
            "auto_dim_text_link": Presentation["auto_dim_text_link"],
        },
        "provenance": {
            "author": Provenance["author"],
            "company": Provenance["company"],
            "comment": Provenance["comment"],
            "created_at": Provenance["created_at"],
            "modified_at": Provenance["modified_at"],
            "updated_at": Provenance["modified_at"],
            "originating_build_code": Provenance["originating_build_code"],
            "license_origin": Provenance["license_origin"],
            "language_id": Presentation["language_id"],
            "cjk_saved": Presentation["cjk_saved"],
        },
        "ui": Presentation["definition"],
        "output": Request["output"],
    }
