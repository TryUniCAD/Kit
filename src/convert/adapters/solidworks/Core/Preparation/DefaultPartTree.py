from convert.adapters.solidworks.Archive.Construction.System.SystemInput import (
    SystemInput,
)


# the ordinary english tree initializes the classified folder roles and canonical supports before assigning model feature ids
def DefaultPartTree(
    PlaneName: str, WrittenAt: int, PlaneAxis: str = "z"
) -> SystemInput:
    PlaneNames = (("x", "Right Plane"), ("y", "Top Plane"), ("z", "Front Plane"))
    return SystemInput(
        (
            ("moCommentsFolder_c", "Comments"),
            ("moFavoriteFolder_c", "Favorites"),
            ("moHistoryFolder_c", "History"),
            ("moSelectionSetFolder_c", "Selection Sets"),
            ("moSensorFolder_c", "Sensors"),
            ("moDocsFolder_c", "Design Binder"),
            ("moSurfaceBodyFolder_c", "Surface Bodies"),
            ("moSolidBodyFolder_c", "Solid Bodies"),
            ("moEnvFolder_c", "Lights and Cameras"),
            ("moInkMarkupFolder_c", "Markups"),
            ("moEqnFolder_c", "Equations"),
            ("moMaterialFolder_c", "Material <not specified>"),
        ),
        tuple(
            (AxisValue, PlaneName if AxisValue == PlaneAxis else NameValue)
            for AxisValue, NameValue in PlaneNames
        ),
        "Annotations",
        "Origin",
        "z",
        WrittenAt,
        True,
    )
