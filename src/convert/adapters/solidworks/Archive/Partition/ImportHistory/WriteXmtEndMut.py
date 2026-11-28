from convert.Geometry.Parasolid import WritePointerMut, WriteTagMut


# transmit and rollback boundaries require the same native kind and null pointer pair
def WriteXmtEndMut(OutputValue: bytearray) -> None:
    WriteTagMut(OutputValue, 1)
    WritePointerMut(OutputValue, 0)
