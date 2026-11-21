from types import MappingProxyType

# concrete virtual dispatch controls inherited node fields independently of archive schema names
KBodyVirtuals = MappingProxyType(
    {
        ("moConfigurationMgr_c", 0x4B8): "moConcept_c.SerializeLWData",
        ("moConfigurationMgr_c", 0x4C0): None,
        ("moConfigurationMgr_c", 0x3F8): False,
        ("moConfigurationMgr_c", 0x3E8): None,
        ("moPartConfiguration_c", 0x4B8): "moConcept_c.SerializeLWData",
        ("moPartConfiguration_c", 0x4C0): None,
        ("moPartConfiguration_c", 0x3F8): True,
        ("moPartConfiguration_c", 0x3E8): "moFeature_c.SerializeXmlData",
        ("moConfiguration_c", 0x4B8): "moConcept_c.SerializeLWData",
        ("moConfiguration_c", 0x4C0): None,
        ("moConfiguration_c", 0x3F8): True,
        ("moConfiguration_c", 0x3E8): "moBaseConfiguration_c.SerializeXmlData",
    }
)
