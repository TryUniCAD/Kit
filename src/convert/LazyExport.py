from __future__ import annotations

from collections.abc import Mapping
from collections.abc import MutableMapping
from importlib.util import find_spec as FindSpec

# shared export contracts keep deferred facades consistent without importing sibling adapter implementations
KExportTable = Mapping[str, tuple[str, str]]


# deferred facade names keep single reader imports from loading every sibling adapter and writer
def LoadExportMut(
    PackageName: str,
    PackageScope: MutableMapping[str, object],
    ExportTable: KExportTable,
    NameText: str,
) -> object:
    ExportInfo = ExportTable.get(NameText)
    ChildName = f"{PackageName}.{NameText}"
    if ExportInfo is None and not (
        NameText.isidentifier()
        and not NameText.startswith("__")
        and FindSpec(ChildName) is not None
    ):
        raise AttributeError(f"module {PackageName!r} has no attribute {NameText!r}")
    # missing names fail first so attribute probes never start the registry package
    from convert.adapters.registry.AdapterDiscovery import LoadExportMod

    if ExportInfo is None:
        return LoadExportMod(ChildName)
    ModuleName, SymbolName = ExportInfo
    ExportValue: object = getattr(LoadExportMod(ModuleName), SymbolName)
    PackageScope[NameText] = ExportValue
    return ExportValue


# interactive discovery keeps listing deferred public names before their first resolution
def ListExports(
    PackageScope: Mapping[str, object],
    ExportTable: KExportTable,
) -> list[str]:
    return sorted({*PackageScope, *ExportTable})
