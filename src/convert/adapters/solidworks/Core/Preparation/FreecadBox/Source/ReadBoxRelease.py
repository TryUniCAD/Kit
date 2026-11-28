from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KReleaseExts,
)

# the exact measured releases define the admitted source property inventories
KBoxReleases = {
    "0.21R33771 (Git)": "0.21",
    "1.0R39319 (Git)": "1.0",
    "1.1R20260928 (Git shallow)": "1.1",
}


# a matching schema number alone does not identify the source property owners
def ReadBoxRelease(VersionValue: str) -> str:
    Release = KBoxReleases.get(VersionValue)
    if Release is None:
        raise ValueError("expected the measured FreeCAD schema-four primitive source")
    return Release


# the source attachment extensions must match the release inventory and order
def ReadBoxExts(Release: str) -> list[dict[str, object]]:
    return [
        {
            "attributes": {
                "name": NameValue,
                "type": ("App::" if NameValue == "SuppressibleExtension" else "Part::")
                + NameValue,
            },
            "tag": "Extension",
        }
        for NameValue in KReleaseExts[Release]
    ]
