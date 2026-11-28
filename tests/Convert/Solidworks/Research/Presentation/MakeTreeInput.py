from __future__ import annotations

from copy import deepcopy as CopyValue
from typing import cast as CastValue


# neutral presentation inputs must distinguish markup roles from annotation notes without saved native data
def MakeTreeInput(Request: dict[str, object]) -> dict[str, object]:
    Neutral = CopyValue(Request)
    Presentation = CastValue(dict[str, object], Neutral["presentation"])
    Presentation["folder_names"] = {
        "moCommentsFolder_c": "Comments",
        "moFavoriteFolder_c": "Favorites",
        "moHistoryFolder_c": "History",
        "moSelectionSetFolder_c": "Selection Sets",
        "moSensorFolder_c": "Sensors",
        "moDocsFolder_c": "Design Binder",
        "moSurfaceBodyFolder_c": "Surface Bodies",
        "moSolidBodyFolder_c": "Solid Bodies",
        "moEnvFolder_c": "Lights and Cameras",
        "moInkMarkupFolder_c": "Markups",
        "moEqnFolder_c": "Equations",
        "moMaterialFolder_c": "Material <not specified>",
    }
    Presentation["cabinet_name"] = "Annotations"
    return Neutral
