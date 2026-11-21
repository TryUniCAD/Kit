from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Drawing.Construction.Indexes.MakeViewKeys import (
    MakeViewKeys,
)
from convert.adapters.solidworks.Drawing.Construction.Indexes.MakeViewProps import (
    MakeViewProps,
)
from convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex import (
    ReadViewIndex,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.CheckViewIntent import (
    CheckViewIntent,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawFile import (
    LinkedDrawFile,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawInput import (
    LinkedDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.MakeLinkedBase import (
    MakeLinkedBase,
)
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawStreams import (
    MakeDrawStreams,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankBuild import (
    MakeBlankBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import (
    MakeBlankFile,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.MakeProjection import (
    MakeProjection,
)
from convert.adapters.solidworks.Drawing.Construction.View.MakeLinkedView import (
    MakeLinkedView,
)
from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import NamedGraph
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
    WriteNamedDef,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.ReadSheetIndex import (
    ReadSheetIndex,
)


# a linked candidate must synthesize its complete drawing around the original sdk child and serialize every stream from the resulting actual owners
def MakeLinkedFile(
    InputValue: LinkedDrawInput, ChildValue: PartCandidate
) -> LinkedDrawFile:
    BaseInput = MakeLinkedBase(InputValue, ChildValue)
    BaseValue = MakeBlankFile(BaseInput)
    SheetValue = InputValue.DrawingValue.Sheets[0]
    IntentValue = SheetValue.Views[0]
    BuildValue = MakeBlankBuild(BaseInput.DrawingValue, BaseInput.OptionsValue)
    Projection = MakeProjection(ChildValue, SheetValue, IntentValue)
    CheckViewIntent(IntentValue, Projection)
    ViewValue = MakeLinkedView(
        BaseValue.ModelGraph,
        ChildValue,
        BuildValue,
        IntentValue,
        Projection,
        InputValue.SupportNames,
    )
    if not isinstance(IntentValue.OrientationName, str):
        raise ValueError(
            "linked drawing requires its qualified explicit named orientation"
        )
    UiValue = NamedGraph(
        BaseValue.UiGraph.DocumentValue,
        BaseInput.UiSettings.VersionValue,
        IntentValue.OrientationName,
    )
    DefinitionValue = WriteNamedDef(UiValue).OutputValue
    StreamsValue = MakeDrawStreams(
        BaseInput,
        BaseValue.HeaderValue,
        BaseValue.ModelGraph.SheetValue.SheetValue,
        DefinitionValue,
    )
    SheetIndex = ReadSheetIndex(BaseValue.ModelGraph.SheetValue.SheetValue)
    ViewIndex = ReadViewIndex(ViewValue)
    StreamsValue[KeywordsStream] = MakeViewKeys(
        BaseInput.OptionsValue.NameValue,
        BaseInput.OptionsValue.CreatedAt,
        SheetIndex,
        ViewIndex,
    )
    StreamsValue["docProps/ISolidWorksInformation.xml"] = MakeViewProps(
        SheetIndex, ViewIndex
    )
    return LinkedDrawFile(
        BaseValue.ModelGraph,
        UiValue,
        BaseValue.HeaderValue,
        ViewValue,
        ChildValue,
        MappingProxyType(StreamsValue),
        BuildSldprt(StreamsValue),
        InputValue.DrawingValue.ActiveSheetId,
        IntentValue.EntityId,
        IntentValue.ModelRefId,
    )
