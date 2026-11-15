from __future__ import annotations

# full base graph coverage requires its real style unit metadata and stream dependencies
KBaseImports = """
from builders.Model import part_graph as NewPartGraph
from builders.Model import clear_model_update as ClearModelUpdate
from builders.Model import mark_model_update as MarkModelUpdate
from builders.Styles import detail_definitions as NewDetails
from builders.Units import unit_table_profile as NewUnits
from builders.Metadata import header as NewHeader
from defs.ConfigPart import load_config as LoadConfig
from defs.ConfigPart import store_config_state as StoreConfigState
from defs.ResolvedCore import load_resolved as LoadResolved
from defs.ResolvedCore import store_resolved as StoreResolved
"""
