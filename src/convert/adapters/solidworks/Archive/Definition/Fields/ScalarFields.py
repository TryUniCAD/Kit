from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# repeated scalar declarations must retain one typed vocabulary without storing document values
def MakeScalarRows(KindName: str, FieldNames: str) -> tuple[NativeField, ...]:
    return tuple(
        NativeField("Scalar", FieldName, KindName) for FieldName in FieldNames.split()
    )
