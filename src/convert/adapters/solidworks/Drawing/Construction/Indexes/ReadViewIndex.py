from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
)
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Drawing.Construction.Indexes.DrawViewIndex import (
    DrawViewIndex,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# the keyword view id is the actual selected configuration id while its filename comes from the real shared child directory entry
def ReadViewIndex(ViewValue: ArchiveNode) -> DrawViewIndex:
    Reference = NeedConceptNode(ViewValue.FieldsValue["f5d8"], "moReferenceInternal_c")
    EntryValue = NeedConceptNode(Reference.FieldsValue["f3b0"], "moExtObject_c")
    FileFields = NeedConceptMap(EntryValue.FieldsValue["shared"])
    ConfigValue = NeedConceptMap(Reference.FieldsValue["f3c0"])
    PathText = NeedConceptNode(FileFields["h18"], "moCStringHandle_c").FieldsValue[
        "value"
    ]
    ModelName = NeedConceptNode(FileFields["h10"], "moCStringHandle_c").FieldsValue[
        "value"
    ]
    ConfigName = ConfigValue["f08"]
    if (
        not isinstance(PathText, CStringValue)
        or not isinstance(ModelName, CStringValue)
        or not isinstance(ConfigName, CStringValue)
    ):
        raise ValueError("drawing indexes require actual typed generated child strings")
    PathValue = PureWindowsPath(PathText.TextValue)
    if (
        FileFields["f20"] != 2
        or not PathValue.is_absolute()
        or PathValue.suffix.casefold() != KPartSuffix
        or PathValue.stem.casefold() != ModelName.TextValue.casefold()
    ):
        raise ValueError(
            "drawing indexes require the qualified matching native child identity"
        )
    NameValue = FieldText(
        NeedConceptNode(ViewValue.FieldsValue["f18"], "moNodeName_c").FieldsValue, "f08"
    )
    CheckDrawText(NameValue, True)
    CheckDrawText(ConfigName.TextValue, True)
    ConfigId = FieldInt(ConfigValue, "f10")
    if not 0 <= ConfigId < 2147483647:
        raise ValueError(
            "drawing view index requires an actual allocated configuration id"
        )
    return DrawViewIndex(NameValue, PathValue, ConfigName.TextValue, ConfigId)
