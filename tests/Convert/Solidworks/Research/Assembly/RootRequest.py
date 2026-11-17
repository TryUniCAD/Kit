from __future__ import annotations

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# an ordinary assembly request supplies its own folder vocabulary and configuration without any native input
def RootRequest(NameValue: str, FractionPreference: float) -> dict[str, object]:
    Shared = MakePartInput([], 0.0, NameValue)
    Presentation = Shared["presentation"]
    assert isinstance(Presentation, dict)
    return {
        "name": NameValue,
        "configuration_name": "Named assembly configuration",
        "origin_name": "Origin",
        "mate_group_name": "Mates",
        "provenance": Shared["provenance"],
        "target": Shared["target"],
        "presentation": {
            "styles": Presentation["styles"],
            "units": Presentation["units"],
            "definition": {
                "drafting_standard": Presentation["drafting_standard"],
                "detail_flags": Presentation["detail_flags"],
                "tessellation": Presentation["tessellation"],
                "system_preference_7a": Presentation["system_preference_7a"],
                "journal_name": NameValue,
                "save_as_part_preferences": {
                    "5fc": False,
                    "5fd": FractionPreference,
                    "5fe": False,
                    "5ff": 0.0,
                    "600": False,
                    "601": True,
                    "602": True,
                    "603": True,
                    "604": True,
                    "605": 0,
                },
            },
            "assembly_features": {
                "plane_names": Presentation["plane_names"],
                "cabinet_name": "Annotations",
                "folder_names": {
                    "moCommentsFolder_c": "Comments",
                    "moFavoriteFolder_c": "Favorites",
                    "moHistoryFolder_c": "History",
                    "moSelectionSetFolder_c": "Selection Sets",
                    "moSensorFolder_c": "Sensors",
                    "moLiveSectionFolder_c": "Live Section Planes",
                    "moDocsFolder_c": "Design Binder",
                    "moEnvFolder_c": "Lights and Cameras",
                    "moInkMarkupFolder_c": "Markups",
                    "moEqnFolder_c": "Equations",
                },
            },
        },
    }
