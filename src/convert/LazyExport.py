from __future__ import annotations

from collections.abc import Mapping
from collections.abc import MutableMapping
from importlib import import_module as ImportModule
from importlib.util import find_spec as FindSpec

# export tables pair each public name with its defining module and attribute
KExportTable = Mapping[str, tuple[str, str]]


# deferred facade names keep single reader imports from loading every sibling adapter and writer
def LoadExportMut(
    PackageName: str,
    PackageScope: MutableMapping[str, object],
    ExportTable: KExportTable,
    NameText: str,
) -> object:
    ExportInfo = ExportTable.get(NameText)
    if ExportInfo is not None:
        ModuleName, SymbolName = ExportInfo
        # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
        ExportValue: object = getattr(ImportModule(ModuleName), SymbolName)
        PackageScope[NameText] = ExportValue
        return ExportValue
    if NameText.isidentifier() and not NameText.startswith("__"):
        ChildName = f"{PackageName}.{NameText}"
        if FindSpec(ChildName) is not None:
            # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
            return ImportModule(ChildName)
    raise AttributeError(f"module {PackageName!r} has no attribute {NameText!r}")


# interactive discovery keeps listing deferred public names before their first resolution
def ListExports(
    PackageScope: Mapping[str, object],
    ExportTable: KExportTable,
) -> list[str]:
    return sorted({*PackageScope, *ExportTable})
