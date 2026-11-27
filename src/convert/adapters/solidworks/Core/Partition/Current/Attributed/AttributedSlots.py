from collections.abc import Mapping
from types import MappingProxyType

# only witnessed attribute layouts can preserve every value owner in the active profile
KAttributedSlots: Mapping[str, tuple[int, tuple[int, ...], tuple[int | None, ...]]] = (
    MappingProxyType(
        {
            "BODY_IN_LIGHTWEIGHT_PERM": (12, (9, 1), (0, 1)),
            "BODY_RECIPE_2001": (12, (9, 1), (0, 0)),
            "ENT_TIME_STAMP_2001": (12, (9, 1), (0, 1)),
            "ATOM_ID_2001": (12, (9, 1), (0, 1)),
            "LAST_BODY_MODIFYING_FEATURE_ID": (12, (9, 1), (0, 1)),
            "SDL/TYSA_TRANSLUCENCY_2": (12, (2,), (1,)),
            "SDL/TYSA_COLOUR_2": (12, (2,), (3,)),
            "SDL/TYSA_DENSITY": (12, (2, 3), (1, 0)),
            "SWIMPLICITBODYNAME_ID_U": (12, (10, 10), (None, 0)),
            "SWEntUnchanged": (14, (1,), (1,)),
            "FACE_ID_2001": (14, (9, 9, 1, 1), (0, 0, None, 2)),
            "DOWNSTREAM_FACE_ID": (14, (1, 1, 1), (6, 0, 0)),
            "LOOP_AUTOMATION_2_2001": (15, (9, 1), (0, 0)),
            "EDGE_AUTOMATION_2_2001": (16, (9, 1), (0, 0)),
            "VERTEX_AUTOMATION_2_2001": (18, (9, 1), (0, 0)),
        }
    )
)


# populated slots need a physical value record rather than a merely resolving pointer
KAttributedValueKinds = MappingProxyType({1: 82, 2: 83, 10: 98})


# the registered owner mask must admit the actual physical class of each attribute
KAttributeOwnerSlots = MappingProxyType({12: 2, 14: 4, 15: 5, 16: 6, 18: 7})
