from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the ordinary local reference constructor excludes alternate context and cached target branches from placement reconstruction
def CheckPrismRef(Reference: ArchiveNode) -> None:
    Fields = Reference.FieldsValue
    ZeroNames = (
        "f68",
        "f18",
        "f1c",
        "f20",
        "f30",
        "f70",
        "f84",
        "fa0",
        "f34",
        "f48",
        "has_fb0",
        "has_fb8",
        "has_fc0",
        "has_fc8",
        "has_fd0",
    )
    if any(Fields.get(FieldName) != 0 for FieldName in ZeroNames):
        raise ValueError("cache free prism support has alternate reference state")
    if (
        any(Fields.get(FieldName) != -1 for FieldName in ("f90", "f94", "f98", "f9c"))
        or Fields.get("f4c") != 19000
    ):
        raise ValueError(
            "cache free prism support has an unqualified reference namespace"
        )
