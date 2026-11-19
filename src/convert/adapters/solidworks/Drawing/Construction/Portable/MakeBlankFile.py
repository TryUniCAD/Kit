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
from convert.adapters.solidworks.Drawing.Construction.Portable.FinishDrawFile import (
    FinishDrawFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankBuild import (
    MakeBlankBuild,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import (
    WriteBlankDef,
)


# blank drawing construction uses the shared compositor after admitting its exact neutral shape
def MakeBlankFile(InputValue: BlankDrawInput) -> DrawingFile:
    CheckBlankInput(InputValue)
    GraphValue = MakeDrawRoot(
        MakeBlankBuild(InputValue.DrawingValue, InputValue.OptionsValue)
    )
    return FinishDrawFile(InputValue, GraphValue, WriteBlankDef)
