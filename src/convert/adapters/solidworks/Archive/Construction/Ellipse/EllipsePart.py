from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# the complete ellipse candidate retains actual linked graph authority alongside generated output
@DataClass(frozen=True, slots=True)
class EllipsePart:
    PlanValue: EllipsePlan
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
