from __future__ import annotations

# fresh graph construction needs the same node factories that the part composer uses
KBuilders = """
from defs.Definition import (
    load_definition as LoadDefinition,
    store_definition as StoreDefinition,
)
from builders.Model import (
    configuration_manager as NewManager,
    principal_planes as NewPlanes,
    PersistentIds,
)
from builders.Model import (
    relation_manager as NewRelations,
    system_folders as NewFolders,
    detail_cabinet as NewCabinet,
)
"""
