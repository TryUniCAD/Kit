from tests.Convert.Solidworks.Research.Construction.RootCaseInput import RootCaseInput


# independently authored system requests must vary configuration shape plane basis and allocation without any saved native input
def SystemCaseInput(NameValue: str, IsVariant: bool) -> dict[str, object]:
    NextValue = 31 if IsVariant else 0
    Request = RootCaseInput(NameValue, NextValue, (31, 34, 40) if IsVariant else (0, 3))
    CreatedAt = 1700000000 + NextValue
    FolderKinds = (
        "moCommentsFolder_c",
        "moDocsFolder_c",
        "moEnvFolder_c",
        "moEqnFolder_c",
        "moFavoriteFolder_c",
        "moHistoryFolder_c",
        "moMaterialFolder_c",
        "moInkMarkupFolder_c",
        "moSelectionSetFolder_c",
        "moSensorFolder_c",
        "moSolidBodyFolder_c",
        "moSurfaceBodyFolder_c",
    )
    FolderValues = [
        [ClassName, NameValue + " " + ClassName] for ClassName in FolderKinds
    ]
    if IsVariant:
        FolderValues.reverse()
    ConfigCount = 3 if IsVariant else 1
    Request.update(
        {
            "version": 19000,
            "target": {"date_code": 2026306, "parasolid_version": 370108},
            "manager": {
                "name": NameValue + " configurations",
                "current": ConfigCount - 1,
                "configurations": [
                    {
                        "name": NameValue + " configuration " + str(IndexValue),
                        "description": NameValue + " intent " + str(IndexValue),
                        "updated_at": CreatedAt + IndexValue,
                    }
                    for IndexValue in range(ConfigCount)
                ],
            },
            "system": {
                "folders": FolderValues,
                "planes": {
                    AxisValue: NameValue + " plane " + AxisValue
                    for AxisValue in ("x", "y", "z")
                },
                "cabinet_name": NameValue + " annotations",
                "origin_name": NameValue + " origin",
                "origin_axis": "x" if IsVariant else "z",
                "created_at": CreatedAt,
                "construction_flag": not IsVariant,
            },
            "provenance": {
                "author": "Kit authored systems",
                "company": "independent SDK construction",
                "created_at": CreatedAt,
                "modified_at": CreatedAt + 20,
                "updated_at": CreatedAt + 10,
                "comment": "generated configuration and system ownership",
            },
        }
    )
    return Request
