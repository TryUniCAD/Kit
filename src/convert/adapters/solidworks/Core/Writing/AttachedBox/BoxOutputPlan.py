from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from pathlib import Path as FilePath

from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.WriteOptions import WriteOptions


# the measured result remains in memory until the actual target transaction writes it
@DataClass(frozen=True, slots=True)
class BoxOutputPlan:
    PathValue: FilePath | None
    SettingsValue: WriteOptions
    Payload: bytes
    EvidenceValue: Mapping[str, object]
    Transfers: tuple[CapTransfer, ...]
