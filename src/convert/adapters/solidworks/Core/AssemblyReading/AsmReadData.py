from collections.abc import Callable
from dataclasses import dataclass as DataClass
from pathlib import Path as FilePath

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Models.DocumentModel import CadDocument


# the assembly reader can resolve fully generated members without accessing their source labels
@DataClass(frozen=True, slots=True)
class AsmReadData:
    IndexValue: dict[str, tuple[FilePath, ...]]
    ReadDocument: Callable[[FilePath, ReadOptions], CadDocument]
    ReadArchive: Callable[[FilePath], SldprtArchive]
