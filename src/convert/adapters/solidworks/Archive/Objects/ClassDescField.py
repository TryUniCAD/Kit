from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# schema and name length must use the same native width in each graph
KClassDescWord = KScalarWords["u16"]

# runtime class names use the same restricted vocabulary across graphs
KClassNameCodec = "ascii"
