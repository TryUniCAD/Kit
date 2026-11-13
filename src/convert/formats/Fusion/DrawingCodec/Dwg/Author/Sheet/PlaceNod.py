from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import SoftPointer
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import EnrolMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceRecord import (
    PlaceRecordMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KNamedObjects,
)

KVersionName = "ACAD_FUSDOC_NOD_VER"
KDocVersion = 45
KVariables = KNamedObjects + "/AcDbVariableDictionary"
KFieldEval = "FIELDEVAL"
KFieldValue = "27"


def PlaceNodMut(Ledger: DraftBook) -> None:
    Version = KNamedObjects + "/" + KVersionName
    _ = EnrolMut(Ledger, KNamedObjects, KVersionName, Version)
    _ = PlaceRecordMut(Ledger, Version, KNamedObjects, (("70", KDocVersion),))
    Variable = KVariables + "/" + KFieldEval
    _ = EnrolMut(Ledger, KVariables, KFieldEval, Variable)
    _ = PlaceMut(
        Ledger,
        Variable,
        "DICTIONARYVAR",
        {
            "ReactorCount": 1,
            "NoXdic": 1,
            "HasDsData": 0,
            "Owner": SoftPointer(KVariables),
            "Reactors": (SoftPointer(KVariables),),
        },
        {"Schema": 0, "VarValue": KFieldValue},
    )
