from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib


# body labels must retain exactly one owning operation without a face history group
def CheckBodyTag(Entity: TagAttrib, Operations: tuple[int, ...]) -> None:
    if (
        len(Entity.Groups) != 1
        or Entity.Groups[0].PrimaryId != str(Operations[0])
        or Entity.Groups[0].OperationIds
        or Entity.Groups[0].ApproachId != 0
    ):
        raise ValueError("Native circular span body label has another operation")
