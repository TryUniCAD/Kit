from convert.formats.Fusion.NativeParam import NativeParam


def CheckParamMeta(Value: NativeParam) -> tuple[bool, bool]:
    Metadata = Value.Metadata
    if type(Metadata) is not bytes:
        raise ValueError("Invalid Fusion numeric metadata")
    if len(Metadata) == 11:
        if Value.BindingId is None or Metadata != bytes(11):
            raise ValueError("Unsupported extended Fusion numeric metadata")
        return False, True
    if (
        len(Metadata) != 10
        or Metadata[:7] != bytes(7)
        or Metadata[7] not in (0, 1)
        or Metadata[8:] != bytes((0, Value.BindingId is None))
    ):
        raise ValueError("Unsupported Fusion numeric metadata")
    return bool(Metadata[7]), False
