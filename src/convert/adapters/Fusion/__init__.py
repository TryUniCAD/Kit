from typing import TYPE_CHECKING

from convert.LazyExport import KExportTable
from convert.LazyExport import ListExports
from convert.LazyExport import LoadExportMut

if TYPE_CHECKING:
    from convert.adapters.Fusion.Adapter import FusionReader
    from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
    from convert.adapters.Fusion.Writer import FusionWriter

# the supported export surface must stay explicit so native adapter translation does not expose incidental implementation imports
__all__ = ("FusionReader", "FusionWriter", "MakeFusionDoc")

# deferred exports keep archive readers from loading the authoring and writer stacks on import
KPublicExports: KExportTable = {
    "FusionReader": ("convert.adapters.Fusion.Adapter", "FusionReader"),
    "FusionWriter": ("convert.adapters.Fusion.Writer", "FusionWriter"),
    "MakeFusionDoc": (
        "convert.adapters.Fusion.Authoring.MakeFusionDoc",
        "MakeFusionDoc",
    ),
}


# module attribute fallback resolves each public adapter name only when a caller first uses it
def __getattr__(NameText: str) -> object:
    return LoadExportMut(__name__, globals(), KPublicExports, NameText)


# interactive discovery still lists deferred adapter names before their first use
def __dir__() -> list[str]:
    return ListExports(globals(), KPublicExports)
