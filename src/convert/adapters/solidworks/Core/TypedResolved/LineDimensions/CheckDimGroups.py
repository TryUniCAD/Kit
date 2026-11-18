from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)


# other native dimension families cannot silently disappear when this bounded rectangle profile is selected
def CheckDimGroups(FieldsValue: Mapping[str, object], HasOrigin: bool = False) -> None:
    for CountName, ArrayName in (
        ("ng1", "val_g1"),
        ("ng3", "val_g3"),
        ("noffset", "offset_dims"),
        ("nlog3", "log_g3"),
        ("niso", "iso"),
        ("nlinpatt", "linear_patterns"),
        ("nlincon", "linear_patt_cons"),
        ("ncircpatt", "circular_patterns"),
        ("ncirccon", "circular_patt_cons"),
        ("n7c0", "list_7c0"),
        ("n9f0", "list_9f0"),
        ("ngroup", "groups"),
    ):
        if ReadDimRows(FieldsValue, CountName, ArrayName):
            raise ValueError("typed rectangle contains another native dimension group")
    if not HasOrigin and ReadDimRows(FieldsValue, "nlog2", "log_g2"):
        raise ValueError("typed rectangle contains an unqualified binary relation")
