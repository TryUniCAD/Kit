from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunFontCase import RunFontCase

# the native parts bind different header identities and preserve distinct authored font values
KFontParts = (
    ("ladder", 69, [62, 62, 69, 69], "CONTINUOUS", 0.003175),
    ("concave", 15, [54, 54, 54, 54], "Continuous", 0.0035),
)

# each sampled span must match its precise embedded native layout
KFontLayouts = (
    "uiLFConfig_c",
    "utLineWidth_c.Serialize.2.0",
    "utCharFormat_c",
    "utLineWidthPrintData_c",
)


# independent decoding of each layout must preserve the link context and raw source values
def TestPartFonts() -> None:
    for CaseName, HeaderIndex, Counters, FontName, Height in KFontParts:
        ReportValue = RunFontCase(CaseName)
        assert ReportValue["anchor_slots"] == [1, 2, 3]
        assert ReportValue["part"] == ["moPart_c", 1, 2]
        assert ReportValue["header_alias"] == ["moExtObject_c", 1, HeaderIndex]
        Records = CastValue(dict[str, dict[str, object]], ReportValue["records"])
        FontValue, LineWidth, Character, PrintWidths = (
            Records[SchemaName] for SchemaName in KFontLayouts
        )
        assert [
            Records[SchemaName]["map_counter"] for SchemaName in KFontLayouts
        ] == Counters
        assert [Records[SchemaName]["bytes"] for SchemaName in KFontLayouts] == [
            32,
            6,
            100,
            32,
        ]
        assert all(RecordValue["map_base"] == 4 for RecordValue in Records.values())
        assert FontValue["fields"] == {
            "f08": FontName,
            "f10": {"f06": 0, "f00": -1},
            "f18": 0,
        }
        assert LineWidth["fields"] == {"f06": 0, "f00": -1}
        CharacterFields = CastValue(dict[str, object], Character["fields"])
        assert CharacterFields["f08"] == "Century Gothic"
        assert CharacterFields["f10"] == Height
        assert (
            PrintWidths["fields_sha256"]
            == "2cb0939bad43ad7292a46eb8dcabf7c343613c0d92d898efb56e68864bf8aa25"
        )
