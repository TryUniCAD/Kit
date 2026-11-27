from typing import TYPE_CHECKING

from convert.LazyExport import KExportTable
from convert.LazyExport import ListExports
from convert.LazyExport import LoadExportMut

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import (
        SldprtWriter as SldprtWriter,
    )

# wildcard imports must retain the writer without exposing deferred facade implementation helpers
__all__ = ("SldprtWriter",)

# the writer stays deferred because part readers must not load native authoring on import
KPublicExports: KExportTable = {
    "SldprtWriter": (
        "convert.adapters.solidworks.Core.Writing.SldprtWriter",
        "SldprtWriter",
    ),
}


# module attribute fallback loads the part writer only when a caller first asks for it
def __getattr__(NameText: str) -> object:
    return LoadExportMut(__name__, globals(), KPublicExports, NameText)


# interactive discovery still lists the deferred writer before its first use
def __dir__() -> list[str]:
    return ListExports(globals(), KPublicExports)
