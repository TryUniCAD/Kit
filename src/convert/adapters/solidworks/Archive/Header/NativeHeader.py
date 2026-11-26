from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef


# callers need typed document identity and bounds without user interface state
@DataClass(frozen=True, slots=True)
class NativeHeader:
    SelfFile: NativeFileRef
    ModelFiles: tuple[NativeFileRef, ...]
    Bounds: tuple[float, ...] | None
