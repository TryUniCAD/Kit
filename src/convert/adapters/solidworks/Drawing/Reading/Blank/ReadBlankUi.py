from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode as NeedNode,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText as ReadText,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require


# document preferences and standard selection must remain explicit when strict reading closes the layout gap
def ReadBlankUi(Document: object) -> ModelDefInput:
    Value = Fields(Document)
    Flags = (Integer(Value["fad8_0"]) & 0xFFFFFFFF) | (
        (Integer(Value["fad8_1"]) & 0xFFFFFFFF) << 32
    )
    Require(
        Value["fa64"] in (0, 1) and Value["fa90"] in (0, 1),
        "blank UI has invalid Boolean preference state",
    )
    Journal = NeedNode(Fields(Value["ffd8"])["f18"], "uoJournal_c")
    return ModelDefInput(
        NeedNode(Value["fba8"]).ClassValue.NameValue,
        tuple(Index for Index in range(64) if Flags & (1 << Index)),
        (
            Integer(Value["fa58"]),
            Integer(Value["fa5c"]),
            Integer(Value["fa60"]),
            bool(Value["fa64"]),
        ),
        bool(Value["fa90"]),
        ReadText(Journal.FieldsValue["f08"]),
        19000,
    )
