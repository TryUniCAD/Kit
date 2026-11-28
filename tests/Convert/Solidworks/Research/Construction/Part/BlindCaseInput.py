from ntpath import join as JoinPath
from typing import cast as CastValue
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)
from tests.Convert.Solidworks.Research.Construction.RootStyleInput import RootStyleInput


# two complete authored documents must vary physical geometry text and target identity without opening any native saved input
def BlindCaseInput(NameValue: str, IsVariant: bool) -> dict[str, object]:
    Dimensions = (37.5, 21.125, 18.625) if IsVariant else (24.0, 16.0, 12.75)
    DocumentValue = MakePlainDoc(NameValue, *Dimensions)
    FolderKinds = (
        "moCommentsFolder_c",
        "moFavoriteFolder_c",
        "moHistoryFolder_c",
        "moSelectionSetFolder_c",
        "moSensorFolder_c",
        "moDocsFolder_c",
        "moSurfaceBodyFolder_c",
        "moSolidBodyFolder_c",
        "moEnvFolder_c",
        "moInkMarkupFolder_c",
        "moEqnFolder_c",
        "moMaterialFolder_c",
    )
    LabelsValue = (
        "Comments",
        "Favorites",
        "History",
        "Selection Sets",
        "Sensors",
        "Design Binder",
        "Surface Bodies",
        "Solid Bodies",
        "Environment",
        "Markups",
        "Equations",
        "Material <not specified>",
    )
    EpochValue = 1794000100 + int(IsVariant) * 1000
    StylesValue = RootStyleInput("sdk plain " + NameValue)
    StylesValue["font_name"] = "Arial"
    return {
        "document": CastValue(object, ToData(DocumentValue)),
        "settings": {
            "styles": StylesValue,
            "document_units": {
                "length_unit": "mm",
                "angle_unit": "degree",
                "unit_system": "mmgs",
                "decimal_places": 4,
            },
            "analysis_units": {
                "length_unit": "m",
                "angle_unit": "radian",
                "unit_system": "mks",
                "decimal_places": 4,
            },
            "system": {
                "folders": list(zip(FolderKinds, LabelsValue, strict=True)),
                "planes": {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"},
                "cabinet_name": "Annotations",
                "origin_name": "Origin",
                "origin_axis": "z",
                "created_at": EpochValue,
                "construction_flag": True,
            },
            "target": {"date_code": 2026306, "parasolid_version": 370108},
            "provenance": {
                "author": "Kit authored neutral input",
                "company": "SDK interoperability research",
                "created_at": EpochValue,
                "modified_at": EpochValue + 10,
                "updated_at": EpochValue + 10,
                "comment": "independent plain rectangular boss",
                "originating_build_code": 2026001,
                "license_origin": 0,
                "cjk_saved": False,
            },
            "definition": {
                "drafting_standard": "moISO_c",
                "detail_flags": [],
                "tessellation": [20, 15, 3, False],
                "system_preference_7a": False,
                "journal_name": "authored journal",
            },
            "output": {
                "path_name": JoinPath(r"C:\KitSdkCandidates", NameValue + ".SLDPRT"),
                "saved_at": EpochValue + 20,
            },
            "hatch_name": "authored hatch",
            "manager_name": "Configurations",
            "density_kg_m3": 1.0,
            "design_intent": False,
            "selected_leader": 0,
        },
    }
