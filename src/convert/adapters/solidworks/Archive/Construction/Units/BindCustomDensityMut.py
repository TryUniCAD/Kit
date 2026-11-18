from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the custom density owner needs its own copy of the document length format and an independent mass selection
def BindCustomDensityMut(
    DensityValue: ArchiveNode, LengthValue: ArchiveNode, MassCode: int
) -> None:
    LengthFields = dict(LengthValue.FieldsValue)
    LengthFields.update({"f88": 0.0, "fb8": None})
    DensityValue.FieldsValue.update(
        {
            "fc4": MassCode,
            "has_fb8": 1,
            "fb8": ArchiveNode(LengthValue.ClassValue, LengthFields),
            "fcc": 0,
        }
    )
