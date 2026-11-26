from struct import pack


def text(value):
    if isinstance(value, tuple):
        marker, value = value
        if marker != "A":
            raise ValueError("independent text expects the ANSI marker")
        raw = value.encode("cp1252")
        return pack("<B", len(raw)) + raw
    raw = value.encode("utf-16-le")
    return pack("<BHB", 255, 65534, len(raw) // 2) + raw


def font(name, difference):
    numbers = (1.75 + difference, -381 + difference, 0.125 + difference,
               0xD00000EF + difference, -0.75 + difference, 0.25 + difference,
               -0.5 + difference, 1.125 + difference, -1.25 + difference, 0xE00000F9 + difference)
    keys = ("f10", "f18", "f20", "f30", "f28", "f38", "f40", "f48", "f50", "f58")
    return {"f08": name, **dict(zip(keys, numbers, strict=True))}, text(name) + pack("<didIdddddI", *numbers)


def annotation():
    face, font_wire = font("Lead λ😀", 7)
    start = (-153, 157, -163, 167, 173)
    leaders = (179, -181, 0.25, 191, 193, -197, -0.375, 199)
    model = {**dict(zip(("f68", "f6c", "f70", "f74", "f78"), start, strict=True)), "f08": face,
             **dict(zip(("f7c", "f80", "f88", "f90", "f94", "f98", "fa0", "fa8"), leaders, strict=True))}
    return model, pack("<iiiiB", *start) + font_wire + pack("<BidiBidi", *leaders)


def authored():
    labels = (("A", "Café"), "sample", "Δ", "other", "", ("A", "fine"), "α", "-", "label 9", "x")
    label_keys = ("f10", "f20", "f18", "f28", "f30", "f38", "f40", "f48", "f50", "f58")
    options = (17, 19, 23, 29, -47, 31, 37, 41, 43, 0.3125, 59)
    option_keys = ("f68", "f6c", "f70", "f74", "f78", "fa0", "fa4", "fa8", "fac", "fb0", "fb8")
    primary, font_wire = font(("A", "Finish É"), 1)
    leader, annotation_wire = annotation()
    model = {"f08": -11, **dict(zip(label_keys, labels, strict=True)),
             **dict(zip(option_keys, options, strict=True)), "fc0": primary, "f120": 67, "f124": 71,
             "f128": leader, "f7c": -73, "f80": -0.625, "f88": "extra λ", "f90": ("A", "près"),
             "f98": -97, "f9c": 101}
    wire = (pack("<i", -11) + b"".join(map(text, labels)) + pack("<BBBBiBBBBdB", *options)
            + font_wire + pack("<BB", 67, 71) + annotation_wire + pack("<id", -73, -0.625)
            + text("extra λ") + text(("A", "près")) + pack("<ii", -97, 101))
    return model, wire
