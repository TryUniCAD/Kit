from ntpath import basename as BaseName, dirname as DirName, join as JoinPath

from convert.adapters.base.ContractTypes import IsDeviceName
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.AsmPathData import (
    AsmPathData,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.CheckNativePath import (
    CheckNativePath,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Container.Format import (
    KAsmSuffix,
)


# one explicit native parent path must determine both actual sibling identities without consulting any source file
def ReadAsmPaths(
    NameValue: str, ChildName: str, NativePath: str, SavedAt: int
) -> AsmPathData:
    ParentPath = CheckNativePath(NativePath)
    RequireAsm(
        ParentPath.stem == NameValue and ParentPath.suffix.casefold() == KAsmSuffix,
        "assembly final filename must match its actual neutral name",
    )
    ChildPath = JoinPath(DirName(NativePath), ChildName + ".SLDPRT")
    RequireAsm(
        not IsDeviceName(ChildName)
        and not ChildName.endswith((".", " "))
        and BaseName(ChildPath) == ChildName + ".SLDPRT"
        and DirName(ChildPath) == DirName(NativePath),
        "child name cannot escape the sibling output folder",
    )
    _ = CheckNativePath(ChildPath)
    RequireAsm(
        BaseName(ChildPath).casefold() != BaseName(NativePath).casefold(),
        "linked native output names collide",
    )
    return AsmPathData(
        SelfFileInput(NativePath, SavedAt, IsAssembly=True),
        SelfFileInput(ChildPath, SavedAt),
    )
