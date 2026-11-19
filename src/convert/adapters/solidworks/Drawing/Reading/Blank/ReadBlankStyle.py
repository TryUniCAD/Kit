from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber as Number,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText as Text,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require
from convert.adapters.solidworks.Drawing.Reading.Blank.Rows import Rows
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankLocale import (
    ReadBlankLocale,
)


# native font vocabulary and line widths must survive instead of disappearing behind a layout projection
def ReadBlankStyle(Model: object, Language: int) -> StyleInput:
    Value = Fields(Fields(Model)["fae0"])
    Language = ReadBlankLocale(Value, Language)
    Widths = Fields(Value["fb0"])
    Exclusions = Rows(Value["f58"])
    Tasks = Fields(Value["fb8"])
    TaskRows = Rows(Tasks["items"])
    Require(Integer(Value["n58"]) == len(Exclusions), "blank style exclusions differ")
    Require(Integer(Tasks["n"]) == len(TaskRows) == 5, "blank style task labels differ")
    Line = Fields(Fields(Fields(Value["f13b0"])["fe0"])["fd0"])
    return StyleInput(
        Integer(Value["f10"]),
        Text(Fields(Value["f90"])["f08"]),
        Text(Line["f08"]),
        Language,
        tuple(Number(Widths[f"f{8+4*Index:x}"]) for Index in range(8)),
        tuple(Text(Fields(Row)["s"]) for Row in Exclusions),
        tuple(Text(Fields(Row)["s"]) for Row in TaskRows),
        tuple(Text(Value[Key]) for Key in ("f200", "f208", "f210")),
    )
