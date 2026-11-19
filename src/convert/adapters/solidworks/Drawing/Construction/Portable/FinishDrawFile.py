from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import (
    MakeSelfFile,
)
from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Container.Container import (
    build_sldprt as BuildContainer,
)
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawHeader import (
    MakeDrawHeader,
)
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawStreams import (
    MakeDrawStreams,
)
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawingFile import (
    DrawingFile,
)
from convert.adapters.solidworks.Drawing.Construction.Ui.MakeDrawDef import MakeDrawDef
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)


# loose drawing metadata and the container must use the same generated header and selected definition graph
def FinishDrawFile(
    InputValue: BlankDrawInput,
    GraphValue: DrawRootGraph,
    EncodeDefinition: Callable[[BlankGraph], DefinitionWire],
) -> DrawingFile:
    HeaderValue = MakeDrawHeader(GraphValue, InputValue.HeaderValue)
    HeaderValue.FieldsValue["f38"] = MakeSelfFile(
        GraphValue.ModelValue, HeaderValue, None, InputValue.FileValue
    )
    GraphValue.ModelValue.FieldsValue["fa8"] = HeaderValue
    UiValue = MakeDrawDef(InputValue.UiSettings, GraphValue)
    StreamsValue = MakeDrawStreams(
        InputValue,
        HeaderValue,
        GraphValue.SheetValue.SheetValue,
        EncodeDefinition(UiValue).OutputValue,
    )
    return DrawingFile(
        GraphValue,
        UiValue,
        HeaderValue,
        MappingProxyType(StreamsValue),
        BuildContainer(StreamsValue),
        InputValue.DrawingValue.ActiveSheetId,
    )
