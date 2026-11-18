from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import (
    MakeSelfFile,
)
from convert.adapters.solidworks.Container.Container import (
    build_sldprt as BuildContainer,
)
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawHeader import (
    MakeDrawHeader,
)
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawStreams import (
    MakeDrawStreams,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawRoot import (
    MakeDrawRoot,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.CheckBlankInput import (
    CheckBlankInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawingFile import (
    DrawingFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankBuild import (
    MakeBlankBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Ui.MakeDrawDef import MakeDrawDef
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import (
    WriteBlankDef,
)


# a complete neutral blank drawing must generate its sdk graph streams and container without a native runtime or saved input
def MakeBlankFile(InputValue: BlankDrawInput) -> DrawingFile:
    CheckBlankInput(InputValue)
    GraphValue = MakeDrawRoot(
        MakeBlankBuild(InputValue.DrawingValue, InputValue.OptionsValue)
    )
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
        WriteBlankDef(UiValue).OutputValue,
    )
    return DrawingFile(
        GraphValue,
        UiValue,
        HeaderValue,
        MappingProxyType(StreamsValue),
        BuildContainer(StreamsValue),
        InputValue.DrawingValue.ActiveSheetId,
    )
