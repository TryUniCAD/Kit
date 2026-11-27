from typing import TYPE_CHECKING

from convert.LazyExport import KExportTable
from convert.LazyExport import ListExports
from convert.LazyExport import LoadExportMut

if TYPE_CHECKING:
    from convert.adapters.base.TransferContract import CarrierReason
    from convert.adapters.base.UsabilityError import ApplicationUsabilityError
    from convert.api import available_adapters
    from convert.api import convert
    from convert.api import extract_brep
    from convert.api import open_document
    from convert.api import registry
    from convert.api import write_document

# this binding preserves the documented public package export surface
__all__ = [
    "available_adapters",
    "ApplicationUsabilityError",
    "CarrierReason",
    "convert",
    "extract_brep",
    "open_document",
    "registry",
    "write_document",
]

# deferred public names keep single format reader imports from building the shared adapter registry
KPublicExports: KExportTable = {
    "ApplicationUsabilityError": (
        "convert.adapters.base.UsabilityError",
        "ApplicationUsabilityError",
    ),
    "AvailableAdapters": ("convert.api", "available_adapters"),
    "CarrierReason": ("convert.adapters.base.TransferContract", "CarrierReason"),
    "ConvertDoc": ("convert.api", "convert"),
    "ExtractBrep": ("convert.api", "extract_brep"),
    "OpenDoc": ("convert.api", "open_document"),
    "RegistryValue": ("convert.api", "registry"),
    "WriteDoc": ("convert.api", "write_document"),
    "available_adapters": ("convert.api", "available_adapters"),
    "convert": ("convert.api", "convert"),
    "extract_brep": ("convert.api", "extract_brep"),
    "open_document": ("convert.api", "open_document"),
    "registry": ("convert.api", "registry"),
    "write_document": ("convert.api", "write_document"),
}


# module attribute fallback resolves public api names only when a caller first uses them
def __getattr__(NameText: str) -> object:
    return LoadExportMut(__name__, globals(), KPublicExports, NameText)


# interactive discovery still lists deferred public names before their first use
def __dir__() -> list[str]:
    return ListExports(globals(), KPublicExports)
