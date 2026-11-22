from dataclasses import dataclass as DataClass
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


# a physical component path is a windows identity while the model name and stamp remain exact
def IndexFileKey(Reference: ArchiveNode) -> tuple[str, PureWindowsPath, int, int]:
    NameValue, Locator, KindValue, Stamp = ReadFileKey(Reference)
    return NameValue, PureWindowsPath(Locator), KindValue, Stamp


# the selected model keeps its root and complete header key for checking occurrence identity across files
@DataClass(frozen=True, slots=True)
class IndexModel:
    RootValue: ArchiveNode
    KeyValue: tuple[str, PureWindowsPath, int, int]
    NameValue: str
