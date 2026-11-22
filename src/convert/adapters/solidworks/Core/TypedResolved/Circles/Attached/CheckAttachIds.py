from collections.abc import Mapping


# the world body identities must agree with this feature atom and active header event
def CheckAttachIds(
    Attrs: Mapping[str, tuple[int, ...]],
    BodyId: int,
    BodyTag: int,
    FeatureId: int,
    HeaderStamp: object,
) -> None:
    if (
        Attrs.get("ATOM_ID_2001") != (BodyId,)
        or Attrs.get("LAST_BODY_MODIFYING_FEATURE_ID") != (FeatureId,)
        or Attrs.get("BODY_MATCH") != (BodyTag,)
        or Attrs.get("ENT_TIME_STAMP_2001") != (HeaderStamp,)
    ):
        raise ValueError(
            "SOLIDWORKS attached circle body attributes disagree with archive ownership"
        )
