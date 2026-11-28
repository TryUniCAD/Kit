from struct import iter_unpack as UnpackWords

from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.BodyTrackIn import (
    BodyTrackIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrIn import (
    CylAttrIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.MakeCylTags import (
    CylTrackWord,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the first body session derives cap selectors and lateral arc references separately from entity tags
def CylAttrIntents(
    BodyValue: XmtNode,
    FaceValues: tuple[XmtNode, XmtNode, XmtNode],
    TagsValue: dict[int, int],
    TrackValue: BodyTrackIn,
) -> tuple[CylAttrIn, ...]:
    Feature = (TrackValue.FeatureId, SignedStamp(TrackValue.FeatureEpoch), 0)
    Primary = (
        (40, *Feature, 1, 0),
        (40, *Feature, 0, 0),
        (74, *Feature, TrackValue.ArcMarker),
    )
    NameUnits = tuple(
        CodeUnit
        for (CodeUnit,) in UnpackWords("<H", TrackValue.FeatureName.encode("utf-16-le"))
    )
    return (
        *(
            CylAttrIn(
                OwnerValue, "FACE_ID_2001", (None, None, ValuesValue, (Position, 0))
            )
            for Position, (OwnerValue, ValuesValue) in enumerate(
                zip(FaceValues, Primary, strict=True), 1
            )
        ),
        CylAttrIn(BodyValue, "BODY_MATCH", ((TagsValue[BodyValue.IndexValue],),)),
        CylAttrIn(BodyValue, "BODY_RECIPE_2001", (None, None)),
        CylAttrIn(
            BodyValue,
            "ENT_TIME_STAMP_2001",
            (None, (SignedStamp(TrackValue.BodyStamp),)),
        ),
        CylAttrIn(BodyValue, "SWIMPLICITBODYNAME_ID_U", (NameUnits, None)),
        CylAttrIn(BodyValue, "BODY_IN_LIGHTWEIGHT_PERM", (None, (1,))),
        *(
            CylAttrIn(
                OwnerValue,
                "SWEntUnchanged",
                (
                    (
                        CylTrackWord(
                            TagsValue[OwnerValue.IndexValue], TrackValue.UpdateStamp
                        ),
                    ),
                ),
            )
            for OwnerValue in FaceValues
        ),
        CylAttrIn(BodyValue, "ATOM_ID_2001", (None, (TrackValue.AtomId,))),
        CylAttrIn(
            BodyValue, "LAST_BODY_MODIFYING_FEATURE_ID", (None, (TrackValue.FeatureId,))
        ),
    )
