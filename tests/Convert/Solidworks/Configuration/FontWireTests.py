from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunFontCase import RunFontCase

# malformed owners need distinct failures at the actual archive field boundary
KFontRefusals = [
    ("truncated_font_text", 0, "string payload is truncated"),
    ("overlong_font_text", 0, "noncanonical length prefix"),
    ("truncated_font_width", 8, "field f10/f00"),
    ("truncated_character", 84, "field f58"),
    ("truncated_print_width", 28, "field f24"),
    ("trailing_font_data", 14, "trailing data"),
    ("wrong_archive_version", 0, "requires archive version 19000"),
    ("unknown_width_layout", 0, "unsupported SOLIDWORKS body schema"),
]


# varied wire values must preserve raw signed and unsigned fields regardless of font content
def TestFontWire() -> None:
    ReportValue = RunFontCase("wire")
    assert ReportValue["map_base"] == 4
    assert ReportValue["map_counter"] == 62
    Records = CastValue(dict[str, dict[str, object]], ReportValue["records"])
    assert Records["uiLFConfig_c"]["fields"] == {
        "f08": ["A", "Kit Ç"],
        "f10": {"f06": -269, "f00": 0.046875},
        "f18": -17131,
    }
    Character = CastValue(dict[str, object], Records["utCharFormat_c"]["fields"])
    assert Character["f08"] == "Å𐐷 text"
    assert Character["f18"] == -19373
    assert Character["f58"] == 0xFA97ED03
    Refusals = CastValue(list[dict[str, object]], ReportValue["refusals"])
    for Refusal, (CaseName, Offset, Diagnostic) in zip(
        Refusals, KFontRefusals, strict=True
    ):
        assert Refusal["case"] == CaseName
        assert Refusal["offset"] == Offset
        assert Diagnostic in CastValue(str, Refusal["diagnostic"])
