from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# internal preparation must return the actual generated owners and bytes without reconstructing a result from saved native payloads
@DataClass(frozen=True, slots=True)
class RevolvePart:
    SystemValue: PartSystem
    ProfileValue: ProfileGraph
    FeatureValue: ArchiveNode
    AxisReference: ArchiveNode
    EndValue: ArchiveNode
    AngleValue: DimensionGraph
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode]
    DefinitionValue: ModelDefGraph
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
    PlanValue: RevolvePlan
    InputValue: PartBuildInput

    # linked consumers need the actual active configuration rather than an inferred identifier or a decoded substitute
    @property
    def CurrentConfig(self) -> ArchiveNode:
        return self.SystemValue.ConfigValues[0]
