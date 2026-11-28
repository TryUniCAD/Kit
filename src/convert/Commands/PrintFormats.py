from json import dumps as DumpJson


# terminal users need a compact capability overview before selecting conversion formats
def PrintFormats(Formats: list[dict[str, object]]) -> None:
    Fields: tuple[str, ...] = ("format", "read", "write", "extensions", "aliases")
    if any("write_extensions" in Format for Format in Formats):
        Fields += ("write_extensions", "write_aliases")
    print("\t".join(Fields))
    for Format in Formats:
        Values = {
            "write_extensions": Format["extensions"] if Format["write"] else (),
            "write_aliases": Format["aliases"] if Format["write"] else (),
            **Format,
        }
        print(
            "\t".join(
                DumpJson(Values[FieldName], ensure_ascii=True) for FieldName in Fields
            )
        )
    print(
        "Registry metadata only; feature, version and conversion acceptance require evidence."
    )
