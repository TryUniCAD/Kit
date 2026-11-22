from collections.abc import Sequence
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoDefs import (
    MakeAnnoDefs,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeCenterData import (
    MakeCenterData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeDatumData import (
    MakeDatumData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeDimDefs import (
    MakeDimDefs,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeFinishData import (
    MakeFinishData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeGtolData import (
    MakeGtolData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLabelDefs import (
    MakeLabelDefs,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeNoteData import (
    MakeNoteData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakePrintWidths import (
    MakePrintWidths,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeSwiftOpts import (
    MakeSwiftOpts,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeTableDefs import (
    MakeTableDefs,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeTargetData import (
    MakeTargetData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeTextArray import (
    MakeTextArray,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeWeldData import (
    MakeWeldData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeDetails(
    *,
    StandardValue: int,
    FontName: str,
    LineStyleName: str,
    LanguageId: int,
    PrintWidths: Sequence[float],
    ExclusionNames: Sequence[str],
    TaskLabels: Sequence[str],
    CutlistExpressions: Sequence[str],
) -> dict[str, object]:
    if type(CastValue(object, StandardValue)) is not int or StandardValue != 1:
        raise ValueError(
            "only the recovered standard-1 construction profile is supported"
        )
    if (
        not isinstance(CastValue(object, CutlistExpressions), Sequence)
        or isinstance(CastValue(object, CutlistExpressions), (str, bytes, bytearray))
        or len(CutlistExpressions) != 3
    ):
        raise ValueError("three authored cut-list id expressions are required")
    TaskArray = MakeTextArray(ValuesInput=TaskLabels)
    if TaskArray["n"] != 5:
        raise ValueError("the five authored task-column labels are required")
    NamesValue = MakeTextArray(ValuesInput=ExclusionNames)
    FieldsValue: dict[str, object] = {
        "f08": 0.002,
        "f10": StandardValue,
        "f13a0": "",
        "f28": 0.0025,
        "f30": 1,
        "f20": 1327104,
        "f24": 2,
        "f3c": 1,
        "f14": 0,
        "f18": 1,
        "f1c": 0,
        "f34": 1,
        "f1388": 0,
        "fec": 2,
        "ff0": 3,
        "ff4": 4,
        "ff8": 1e-05,
        "f100": 1.4e-05,
        "f108": 2.5e-06,
        "f110": 2,
        "f114": 3,
        "f118": 4,
        "f120": 0.00017453292519943334,
        "f128": 0.0002443460952792067,
        "f130": 4.3633231299858336e-05,
        "f138": int(CastValue(object, StandardValue) != 0),
        "f140": 0.0005,
        "f148": 0.008726646259971667,
        "fe8": 1,
        "f150": 0,
        "f154": 1,
        "f158": 1,
        "f164": 1,
        "f168": 1,
        "f16c": 1,
        "f170": 0,
        "f174": 0,
        "f40": 0,
        "f138c": 1,
        "f1390": 0,
        "f1394": 0,
        "f1398": 0,
        "f44": 0,
        "f48": 0,
        "fe0": -1,
        "fe2": -1,
        "f50": 1,
        "f4c": 0,
        "f2bc0": 0.008,
        "f2bc8": 0,
        "f2bd8": "",
        "f2be0": 0,
        "f2be8": "",
        "f2bf0": 1,
        "f178": 0,
        "f17c": 0,
        "f1a8": 0,
        "f1ac": 0,
        "f1b0": 0,
        "f1b4": 0,
        "f180": 1,
        "f184": 1,
        "f188": 1,
        "f18c": 1,
        "f190": 1,
        "f194": 1,
        "n58": NamesValue["n"],
        "f58": NamesValue["items"],
        "f198": 1,
        "f1a0": 0,
        "f1a4": 0,
        "fb8": TaskArray,
        "f90": MakeCharFormat(FontName=FontName, HeightValue=0.0035, PointHeight=0),
        "f13b0": MakeDimDefs(FontName=FontName, LineStyleName=LineStyleName),
        "f1f18": MakeAnnoDefs(FontName=FontName, LanguageId=LanguageId),
        "f2410": MakeTableDefs(FontName=FontName),
        "f2750": MakeLabelDefs(FontName=FontName),
        "f2e8": MakeFinishData(FontName=FontName),
        "f4d8": MakeNoteData(FontName=FontName),
        "f730": MakeWeldData(FontName=FontName),
        "f9a0": MakeGtolData(FontName=FontName),
        "fb88": MakeCenterData(FontName=FontName),
        "fcd8": MakeDatumData(FontName=FontName),
        "fde0": MakeTargetData(FontName=FontName),
        "ff68": MakeSwiftOpts(),
        "fb0": MakePrintWidths(WidthsValue=PrintWidths),
        "f2bd0": 5000.0,
        "f2bf4": 3,
        "f2bf8": 1,
        "f2bfc": 0,
        "f2c00": 0,
        "f2c0c": 1,
        "f2c10": 0,
        "f54": 1,
        "f2c04": 1,
        "f2c08": 1,
        "f80": 1,
        "f88": 0.0025,
        "f2c18": 0.0085,
        "f2c20": 0.0085,
        "f2c28": 0.0085,
        "f2c30": 3.0,
        "f2c38": 3.0,
        "f2c40": 0,
        "f2c44": 0,
        "f2c48": -1,
        "f2c4c": 0,
        "f2c50": 0,
        "f2c54": 1,
        "f2c58": 1,
        "f2c5c": 1,
        "f98": 0,
        "fa0": MakeCharFormat(FontName=FontName, HeightValue=-1, PointHeight=12),
        "fa8": MakeCharFormat(FontName=FontName, HeightValue=-1, PointHeight=12),
        "f2c64": 0,
        "f2c68": 0,
        "f19c": 0,
        "f1bc": 1,
        "f1c0": "Plate,",
        "f1c8": "",
        "f1d0": "x",
        "f1d8": "x",
        "f1e0": 2,
        "f1e4": 3,
        "f1e8": 1,
        "f1f8": 1,
        "f1f0": "Sheet",
        "f1fc": 0,
        "f15c": 1,
        "f160": 1,
        "f218": 0,
        "f200": ReadStyleText(CutlistExpressions[0], "cut-list id expression"),
        "f208": ReadStyleText(CutlistExpressions[1], "cut-list id expression"),
        "f210": ReadStyleText(CutlistExpressions[2], "cut-list id expression"),
        "f220": 1,
        "f224": 0,
        "f2c6c": 0,
        "f21c": 0,
        "f1b8": 0,
    }
    for OriginValue in (552, 648):
        FieldsValue.update(
            {
                f"f{OriginValue + 32 * GroupValue + 4 * ItemValue:x}": 0
                for GroupValue in range(3)
                for ItemValue in range(8)
            }
        )
    return FieldsValue
