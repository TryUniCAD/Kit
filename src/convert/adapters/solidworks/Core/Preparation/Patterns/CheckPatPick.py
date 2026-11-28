from interchange.geometry.Models.Selection import Selection, SelectPathElem


# every native reference must preserve its actual portable local owner
def CheckPatPick(
    PickValue: Selection, KindValue: str, TargetId: str, DetailName: str = ""
) -> None:
    if (
        PickValue.path != (SelectPathElem(KindValue, TargetId, DetailName),)
        or PickValue.query
        or PickValue.point is not None
        or PickValue.provenance is not None
        or PickValue.attributes
    ):
        raise ValueError(
            "neutral selection does not name its exact local "
            + (DetailName or KindValue)
            + " owner"
        )
