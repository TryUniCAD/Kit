from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords


# native numeric conversion and range failures must complete before buffers are mutated
def EncodeScalar(NumberValue: object, KindName: str) -> bytes:
    return KScalarWords[KindName].pack(NumberValue)
