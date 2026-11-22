from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrDef import (
    CylAttrDef,
)

# the body bookkeeping fields share the ordinary pointer and integer contract
KBodyScalar = CylAttrDef((2,), (9, 1), (0, 0, 0, 0, 3, 5, 0, 0))

# the world registers only the definitions installed by this typed attachment
KCylAttrDefs = MappingProxyType(
    {
        "FACE_ID_2001": CylAttrDef((4,), (9, 9, 1, 1), (0, 0, 0, 0, 3, 6, 0, 0)),
        "BODY_MATCH": CylAttrDef((2,), (1,), (1,) * 8),
        "BODY_RECIPE_2001": KBodyScalar,
        "ENT_TIME_STAMP_2001": KBodyScalar,
        "SWIMPLICITBODYNAME_ID_U": CylAttrDef(
            (2, 4, 5, 6, 9), (10, 10), KBodyScalar.ActionsValue
        ),
        "BODY_IN_LIGHTWEIGHT_PERM": KBodyScalar,
        "SWEntUnchanged": CylAttrDef((4, 6), (1,), (1,) * 8),
        "ATOM_ID_2001": KBodyScalar,
        "LAST_BODY_MODIFYING_FEATURE_ID": KBodyScalar,
    }
)
