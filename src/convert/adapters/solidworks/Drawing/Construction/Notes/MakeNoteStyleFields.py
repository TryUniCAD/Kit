from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineWidth import (
    MakeLineWidth,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# explicit note appearance follows the actual document style and keeps frame and leader width owners distinct
def MakeNoteStyleFields(StyleValue: Mapping[str, object]) -> dict[str, object]:
    FrameValue = FieldInt(StyleValue, "f34")
    WidthValue = (
        dict(NeedConceptMap(StyleValue["f2c"]))
        if FrameValue
        else MakeLineWidth(CategoryValue=0, WidthValue=-1.0)
    )
    return {
        "f390": StyleValue["f20"],
        "f2f4": FrameValue,
        "f2f8": WidthValue,
        "f308": StyleValue["f40"],
        "f30c": dict(NeedConceptMap(StyleValue["f38"])),
    }
