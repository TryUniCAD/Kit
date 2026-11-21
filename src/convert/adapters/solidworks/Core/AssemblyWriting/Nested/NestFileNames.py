from pathlib import PureWindowsPath

from convert.adapters.solidworks.Container.Format import KAsmSuffix
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAssemblyPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.CheckNativePath import (
    CheckNativePath,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm


# collision preflight uses every owned definition and the actual mapped windows directory
def NestFileNames(
    PlanValue: NestedAssemblyPlan, NativeValue: str
) -> tuple[PureWindowsPath, ...]:
    RootPath = CheckNativePath(NativeValue)
    RequireAsm(
        RootPath.stem == PlanValue.RootValue.name
        and RootPath.suffix.casefold() == KAsmSuffix,
        "nested assembly destination must retain the modeled root basename",
    )
    PathValues: list[PureWindowsPath] = []
    for Definition in PlanValue.OrderedDefinitions:
        SuffixValue = ".SLDPRT" if Definition.id in PlanValue.LeafValues else ".SLDASM"
        NameValue = Definition.name + SuffixValue
        if Definition is PlanValue.RootValue:
            PathValues.append(RootPath)
            continue
        PathValue = CheckNativePath(str(RootPath.parent / NameValue))
        RequireAsm(
            PathValue.parent == RootPath.parent and PathValue.name == NameValue,
            "nested definition destination must be a distinct sibling filename",
        )
        PathValues.append(PathValue)
    RequireAsm(
        PathValues[-1] == RootPath
        and len({Value.name.casefold() for Value in PathValues}) == len(PathValues),
        "nested assembly file plan has colliding or misplaced definitions",
    )
    return tuple(PathValues)
