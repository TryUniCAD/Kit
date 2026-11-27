from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from pathlib import Path as FilePath

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange import CadDocument


# typed mate projection must reuse already resolved component documents and their exact physical sources
@DataClass(frozen=True, slots=True)
class PublicMateEnv:
    NativeValue: NativeAsm
    ArchiveValue: SldprtArchive
    PathsValue: Mapping[int, FilePath]
    DocumentsValue: Mapping[int, CadDocument]
    SourceKey: str
