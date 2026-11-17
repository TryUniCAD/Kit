from __future__ import annotations

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# an ordinary assembly request supplies its own folder vocabulary and configuration without any native input
def RootRequest(NameValue: str) -> dict[str, object]:
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
