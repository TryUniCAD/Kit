from struct import pack, unpack

FONT = "uiLFConfig_c"
WIDTH = "utLineWidth_c.Serialize.2.0"
CHARACTER = "utCharFormat_c"
PRINT = "utLineWidthPrintData_c"
CHAR_FORMAT = "<didIdddddI"
CHAR_KEYS = ("f10", "f18", "f20", "f30", "f28", "f38", "f40", "f48", "f50", "f58")
PRINT_KEYS = ("f8", "fc", "f10", "f14", "f18", "f1c", "f20", "f24")


def take_short_text(data):
    wide = data.startswith(b"\xff\xfe\xff")
    prefix = 3 if wide else 0
    units = data[prefix]
    end = prefix + 1 + units * (2 if wide else 1)
    if units == 0xFF or end > len(data):
        raise ValueError("reference expects one complete short CString")
    body = data[prefix + 1:end]
    return body.decode("utf-16-le") if wide else ("A", body.decode("latin-1")), end


def read_reference(data, layout):
    if layout == WIDTH:
        style, width = unpack("<hf", data)
        return {"f06": style, "f00": width}
    if layout == PRINT:
        return dict(zip(PRINT_KEYS, unpack("<8f", data), strict=True))
    text, end = take_short_text(data)
    if layout == FONT:
        style, width, suffix = unpack("<hfh", data[end:])
        return {"f08": text, "f10": {"f06": style, "f00": width}, "f18": suffix}
    if layout == CHARACTER:
        return {"f08": text, **dict(zip(CHAR_KEYS, unpack(CHAR_FORMAT, data[end:]), strict=True))}
    raise ValueError("unrecognized reference formatting layout")


def author_records():
    chars = (-0.375, -19373, 0.8125, 0xD1345761, -13.5, 4.25, -2.0, 3.0, -8.5, 0xFA97ED03)
    prints = (-13.25, 22.875, -0.0625, 0.5, 3.25, 74.375, -11.75, 2.125)
    style, width, suffix = -269, 0.046875, -17131
    line_font = "Kit Ç"
    char_font = "Å𐐷 text"
    line_bytes = line_font.encode("latin-1")
    char_bytes = char_font.encode("utf-16-le")
    return {
        FONT: (
            bytes((len(line_bytes),)) + line_bytes + pack("<hfh", style, width, suffix),
            {"f08": ("A", line_font), "f10": {"f06": style, "f00": width}, "f18": suffix},
        ),
        WIDTH: (pack("<hf", style, width), {"f06": style, "f00": width}),
        CHARACTER: (
            b"\xff\xfe\xff" + bytes((len(char_bytes) // 2,)) + char_bytes + pack(CHAR_FORMAT, *chars),
            {"f08": char_font, **dict(zip(CHAR_KEYS, chars, strict=True))},
        ),
        PRINT: (pack("<8f", *prints), dict(zip(PRINT_KEYS, prints, strict=True))),
    }


def malformed_records(records):
    font, _ = records[FONT]
    char, _ = records[CHARACTER]
    printing, _ = records[PRINT]
    width_offset = 1 + font[0]
    return (
        ("truncated_font_text", FONT, font[:width_offset - 1], 19000, "string payload is truncated"),
        ("overlong_font_text", FONT, b"\xff" + pack("<H", font[0]) + font[1:], 19000,
         "noncanonical length prefix"),
        ("truncated_font_width", FONT, font[:width_offset + 5], 19000,
         "field f10/f00"),
        ("truncated_character", CHARACTER, char[:-1], 19000, "field f58"),
        ("truncated_print_width", PRINT, printing[:-1], 19000, "field f24"),
        ("trailing_font_data", FONT, font + b"\x00", 19000, "trailing data"),
        ("wrong_archive_version", FONT, font, 18900, "requires archive version 19000"),
        ("unknown_width_layout", "utLineWidth_c.Serialize.1.0", records[WIDTH][0], 19000,
         "unsupported SOLIDWORKS body schema"),
    )
