from types import MappingProxyType

# these native roles select the appropriate existing node and folder callbacks
KSaveTreeVirts = MappingProxyType(
    {
        ("moHistoryFeatItemData_c", 1000): None,
        ("moHistoryFeatItemData_c", 1016): True,
        ("moHistoryFeatItemData_c", 1208): "moNode_c.SerializeLWData",
        ("moHistoryFeatItemData_c", 1216): None,
        ("moNotesAreaFtrFolder_c", 1000): "moFeature_c.SerializeXmlData",
        ("moNotesAreaFtrFolder_c", 1016): True,
        ("moNotesAreaFtrFolder_c", 1208): "moConcept_c.SerializeLWData",
        ("moNotesAreaFtrFolder_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moNotesAreaFtrFolder_c", 2624): True,
    }
)
