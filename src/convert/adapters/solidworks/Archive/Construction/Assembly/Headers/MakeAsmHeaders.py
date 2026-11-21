from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeader import (
    MakeAsmHeader,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import (
    MakeSharedCopy,
)
from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import (
    MakeSelfFile,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# both assembly headers must share one generated self record whose handles can also serve the separately rooted embedded configuration body graph
def MakeAsmHeaders(
    StateValue: AssemblyState, InputValue: AssemblyInput
) -> tuple[ArchiveNode, ArchiveNode]:
    HeaderValue = MakeAsmHeader(StateValue, InputValue.HeaderValue, True)
    TopHeader = MakeAsmHeader(StateValue, InputValue.HeaderValue, False)
    SelfValue = MakeSelfFile(
        StateValue.RootValue,
        HeaderValue,
        StateValue.CurrentConfig,
        InputValue.OutputValue,
    )
    SelfValue.FieldsValue["shared"] = MakeSharedCopy(SelfValue)
    HeaderValue.FieldsValue["f38"] = SelfValue
    TopHeader.FieldsValue["f38"] = SelfValue
    return HeaderValue, TopHeader
