from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KAngleCodes,
    KLengthCodes,
    KMassCodes,
    KSystemCodes,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode as Node,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require
from convert.adapters.solidworks.Drawing.Reading.Blank.Rows import Rows


# document unit choices must retain their actual precision and mass ownership before reconstruction
def ReadBlankUnits(Model: object) -> UnitInput:
    Table = Node(Fields(Model)["f9b8"], "moUnitsTable_c").FieldsValue
    Items = Rows(Table["items"])
    Require(
        Integer(Table["n"]) == len(Items) == 16,
        "blank units require sixteen complete owners",
    )
    Nodes = tuple(Node(Fields(Row)["o"]) for Row in Items)
    Units = {Value.ClassValue.NameValue: Value.FieldsValue for Value in Nodes}
    Require(len(Units) == 16, "blank units contain duplicate classes")
    Precisions = {Integer(Value["f0c"]) for Value in Units.values()}
    Require(
        len(Precisions) == 1,
        "blank constructor cannot represent distinct format precisions",
    )
    Length = {Code: Name for Name, Code in KLengthCodes.items()}[
        Integer(Units["moLengthUserUnits_c"]["fb0"])
    ]
    Angle = {Code: Name for Name, Code in KAngleCodes.items()}[
        Integer(Units["moAngleUserUnits_c"]["fb0"])
    ]
    System = {Code: Name for Name, Code in KSystemCodes.items()}[
        Integer(Units["moUnitSysUnits_c"]["fb0"])
    ]
    Mass = (
        None
        if System != "custom"
        else {Code: Name for Name, Code in KMassCodes.items()}[
            Integer(Units["moDensityUnits_c"]["fc4"])
        ]
    )
    return UnitInput(Length, Angle, System, Precisions.pop(), Mass)
