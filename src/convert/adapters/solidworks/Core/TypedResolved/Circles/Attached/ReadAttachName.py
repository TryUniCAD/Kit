from collections.abc import Mapping


# the portable label comes from the actual implicit native body name
def ReadAttachName(Attrs: Mapping[str, tuple[int, ...]]) -> str:
    Label = b"".join(
        UnitValue.to_bytes(2, "little")
        for UnitValue in Attrs["SWIMPLICITBODYNAME_ID_U"]
    ).decode("utf-16-le")
    if (
        not Label
        or "\x00" in Label
        or any(
            NameValue in Attrs
            for NameValue in (
                "SDL/TYSA_NAME",
                "SDL/TYSA_UNAME",
                "SW_INTERNAL_BODY_NAME",
            )
        )
    ):
        raise ValueError("SOLIDWORKS attached circle has an invalid implicit body name")
    return Label
