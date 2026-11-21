from dataclasses import dataclass as DataClass
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


@DataClass(frozen=True, slots=True)
class OriginChild:
    PathValue: PureWindowsPath
    Sha256Value: str
    LinkValue: NativeLink
    ManagerValue: CmgrGraph
