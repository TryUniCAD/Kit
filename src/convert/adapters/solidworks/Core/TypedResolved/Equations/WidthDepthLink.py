from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph


# the public binding needs the proven configuration and distinct native expression identities together
@DataClass(frozen=True, slots=True)
class WidthDepthLink:
    ConfigValue: ConfigGraph
    SourceText: str
    RightText: str
    WidthFeature: int
    DepthFeature: int
    RelationOwner: Mapping[str, object]
    WidthOwner: Mapping[str, object]
    DepthOwner: Mapping[str, object]
