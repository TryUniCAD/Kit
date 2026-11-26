from json import dumps as DumpJson


# terminal users need a compact capability overview before selecting conversion formats
def PrintFormats(Formats: list[dict[str, object]]) -> None:
    Fields: tuple[str, ...] = ("format", "read", "write", "extensions")
    if any("write_extensions" in Format for Format in Formats):
        Fields += ("write_extensions",)
    print("\t".join(Fields))
    for Format in Formats:
        Values = {
            "write_extensions": Format["extensions"] if Format["write"] else (),
            **Format,
        }
        print(
            "\t".join(
                DumpJson(Values[FieldName], ensure_ascii=True) for FieldName in Fields
            )
        )
