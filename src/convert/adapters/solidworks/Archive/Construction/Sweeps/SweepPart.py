from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.SweepProfiles import (
    SweepProfiles,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# downstream consumers can retain the actual swept boss graph and its two driver owners alongside the emitted part
@DataClass(frozen=True, slots=True)
class SweepPart:
    SystemValue: PartSystem
    ProfilesValue: SweepProfiles
    FeatureValue: ArchiveNode
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
