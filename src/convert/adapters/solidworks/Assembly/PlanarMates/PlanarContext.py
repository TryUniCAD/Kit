from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from typing import TYPE_CHECKING as TypeChecking

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

if TypeChecking:
    from convert.adapters.solidworks.Assembly.Assembly import NativeAsmA, NativeAsmItem


# the selected part configuration supplies its actual header and persistent datum owners
@DataClass(frozen=True, slots=True)
class PlanarChild:
    HeaderNode: ArchiveNode
    DatumNodes: Mapping[int, ArchiveNode]


# linked mate references need the model graph and its independent assembly identity index
@DataClass(frozen=True, slots=True)
class PlanarContext:
    ModelNode: ArchiveNode
    OccurrenceMap: Mapping[int, NativeAsmItem]
    DefinitionMap: Mapping[int, NativeAsmA]
    ChildMap: Mapping[tuple[str, int], PlanarChild]
