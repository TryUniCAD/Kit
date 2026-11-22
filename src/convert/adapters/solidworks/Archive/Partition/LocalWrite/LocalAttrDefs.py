from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# these definitions identify the current local body bookkeeping roles in registration order
KLocalAttrNames = (
    "ATOM_ID_2001",
    "LAST_BODY_MODIFYING_FEATURE_ID",
    "SWIMPLICITBODYNAME_ID_U",
    "ENT_TIME_STAMP_2001",
    "BODY_RECIPE_2001",
)


# each local definition has its own name member and no world definition chain
def LocalAttrDefs(FirstIndex: int) -> tuple[XmtNode, ...]:
    NodesValue: list[XmtNode] = []
    for IndexValue, NameValue in enumerate(KLocalAttrNames):
        DefinitionIndex = FirstIndex + 2 * IndexValue
        IsNameValue = NameValue == "SWIMPLICITBODYNAME_ID_U"
        OwnersValue = (2, 4, 5, 6, 9) if IsNameValue else (2,)
        NodesValue.extend(
            (
                XmtNode(
                    DefinitionIndex,
                    80,
                    {
                        "next": 0,
                        "identifier": DefinitionIndex + 1,
                        "type_id": 9000,
                        "actions": (0, 0, 0, 0, 3, 5, 0, 0),
                        "field_names": 0,
                        "legal_owners": tuple(
                            int(SlotValue in OwnersValue) for SlotValue in range(17)
                        ),
                        "fields": (10, 10) if IsNameValue else (9, 1),
                    },
                ),
                XmtNode(DefinitionIndex + 1, 79, {"string": NameValue}),
            )
        )
    return tuple(NodesValue)
