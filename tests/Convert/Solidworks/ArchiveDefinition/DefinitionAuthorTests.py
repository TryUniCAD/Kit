from hashlib import sha256 as Digest
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.ArchiveDefinition.RunDefProcess import RunDefProcess

# one shared set of authored settings isolates the journal length change
KDefOptions = {
    "standard": "moISO_c",
    "bits": [1, 31, 34, 63],
    "tessellation": [26, 4, 25, True],
    "compression": False,
    "density": 2843.25,
}


# generated stream growth must account for actual wide text and its extended frame
def TestDefAuthor(TmpPath: FilePath) -> None:
    ShortText = "Workshop log"
    AddedText = "\U00020000" * 128
    SizeValues: list[int] = []
    for TextValue in (ShortText, ShortText + AddedText):
        InputValue = DumpJson({**KDefOptions, "journal": TextValue}).encode("utf-8")
        WireValue = RunDefProcess(TmpPath, "author", InputValue)
        Report = CastValue(
            dict[str, object], LoadJson(RunDefProcess(TmpPath, "readback", WireValue))
        )
        SizeValues.append(len(WireValue))
        assert Report["size"] == len(WireValue)
        assert Report["sha256"] == Digest(WireValue).hexdigest()
        assert Report["typed_wire_equal"] is True and Report["next_map_index"] == 7
        assert Report["root"] == ["uiPartDoc_c", 1]
        assert Report["density_kg_m3"] == KDefOptions["density"]
        assert Report["display_words"] == [-2147483646, -2147483644]
        assert Report["journal"] == {
            "schema": 0,
            "sha256": Digest(TextValue.encode("utf-8")).hexdigest(),
            "units": len(TextValue.encode("utf-16-le")) // 2,
        }
        assert Report["renderer_empty_wrapper"] is None
    assert SizeValues[1] - SizeValues[0] == len(AddedText.encode("utf-16-le")) + 2
