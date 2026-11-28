from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import (
    DepthOwner as EndDepthOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the public binding needs the proven configuration and distinct native expression identities together
@DataClass(frozen=True, slots=True)
class WidthDepthLink:
    SourceValue: SldprtArchive
    LinkValue: NativeLink
    SourceText: str
    RightText: str
    WidthFeature: int
    DepthFeature: int
    RelationOwner: Mapping[str, object]
    WidthOwner: Mapping[str, object]
    DepthOwner: Mapping[str, object]
    RelationNodes: frozenset[ArchiveNode]
    WidthParam: str
    DepthParam: str
    DormantValue: EndDepthOwner | None = None

    # configuration reporting consumes the same graph that validated the relation
    @property
    def ConfigValue(Instance) -> ConfigGraph:
        return Instance.LinkValue.ConfigValue
