from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the sole configuration still needs its ordinary constructor selectors because alternate flags can change history interpretation without adding another object
def CheckCfgMode(ConfigValue: ArchiveNode) -> None:
    Fields = ConfigValue.FieldsValue
    ModesValue = (
        ("f28", 0x40000000),
        ("f2b0", 19000),
        ("f4b0", -1),
        ("f4c4", 0x100),
        ("f9a8", 19000),
        ("f96c", 1),
        ("faf0", 0),
        ("faf4", 1),
        ("f788", 1),
        ("f78c", -1.0),
        ("f790", -1.0),
        ("fb30", 1),
        ("f844", 1),
        ("f750", -1),
        ("fbd4", 1),
        ("fc50", -1.0),
        ("fccc", -1),
        ("fcd4", -1),
        ("fcd0", -1),
    )
    if any(Fields.get(FieldName) != ModeValue for FieldName, ModeValue in ModesValue):
        raise ValueError(
            "cache free prism has alternate configuration constructor selectors"
        )
    if Fields.get("f498") != "" or any(
        Fields.get(FieldName) is not None
        for FieldName in ("f6a0", "f660", "fb80", "fbd8", "fc48", "fcb8", "fcc0")
    ):
        raise ValueError("cache free prism has additional configuration owners")
