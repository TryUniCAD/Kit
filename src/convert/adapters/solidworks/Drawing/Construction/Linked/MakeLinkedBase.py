from dataclasses import replace as ReplaceValue
from ntpath import basename as BaseName, splitext as SplitExt

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldText
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawInput import (
    LinkedDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingView import DrawingView


# the transient blank base may omit a view only after all original portable links are bound to the actual generated child for later complete attachment
def MakeLinkedBase(
    InputValue: LinkedDrawInput, ChildValue: PartCandidate
) -> BlankDrawInput:
    if type(InputValue) is not LinkedDrawInput or type(ChildValue) is not PartCandidate:
        raise TypeError(
            "linked drawing construction requires typed intent and the actual SDK part"
        )
    DrawingValue = InputValue.DrawingValue
    if (
        type(DrawingValue) is not DrawingData
        or len(DrawingValue.Sheets) != 1
        or len(DrawingValue.ModelRefs) != 1
        or len(DrawingValue.Sheets[0].Views) != 1
    ):
        raise ValueError("linked drawing requires exactly one sheet model and view")
    SheetValue, Reference = DrawingValue.Sheets[0], DrawingValue.ModelRefs[0]
    ViewValue = SheetValue.Views[0]
    if type(ViewValue) is not DrawingView or type(Reference) is not DrawingModelRef:
        raise TypeError(
            "linked drawing requires actual portable model reference and view records"
        )
    for Identifier in (SheetValue.EntityId, ViewValue.EntityId, Reference.EntityId):
        CheckDrawText(Identifier, False)
    if (
        len({SheetValue.EntityId, ViewValue.EntityId, Reference.EntityId}) != 3
        or ViewValue.ModelRefId != Reference.EntityId
    ):
        raise ValueError(
            "linked drawing identities must be unique and resolve to the one generated child"
        )
    ChildFile = NeedConceptNode(
        ChildValue.HeaderValue.FieldsValue["f38"], "moExtObject_c"
    )
    FileFields = NeedConceptMap(ChildFile.FieldsValue["shared"])
    PathValue = NeedConceptNode(FileFields["h18"], "moCStringHandle_c").FieldsValue[
        "value"
    ]
    ChildName = FieldText(
        NeedConceptNode(
            ChildValue.SystemValue.RootValue.FieldsValue["f18"], "moNodeName_c"
        ).FieldsValue,
        "f08",
    )
    ConfigName = FieldText(
        NeedConceptNode(
            ChildValue.CurrentConfig.FieldsValue["f18"], "moNodeName_c"
        ).FieldsValue,
        "f08",
    )
    CheckDrawText(ChildName, True)
    CheckDrawText(ConfigName, True)
    if (
        not isinstance(PathValue, CStringValue)
        or Reference.SourceFormatId != KPartFormatId
        or Reference.SourcePath != PathValue.TextValue
        or SplitExt(BaseName(PathValue.TextValue))[0].casefold() != ChildName.casefold()
        or ViewValue.ConfigurationName != ConfigName
        or InputValue.FileValue.PathName == PathValue.TextValue
    ):
        raise ValueError(
            "linked drawing path model or configuration differs from its actual generated child"
        )
    BaseDrawing = ReplaceValue(
        DrawingValue, Sheets=(ReplaceValue(SheetValue, Views=()),), ModelRefs=()
    )
    return BlankDrawInput(
        BaseDrawing,
        InputValue.OptionsValue,
        InputValue.UiSettings,
        InputValue.HeaderValue,
        InputValue.FileValue,
        InputValue.HistoryValue,
    )
