from __future__ import annotations

from Core import DOCUMENT_VERSION_2026
from convert.adapters.solidworks.Archive.Definition.Construction.MakeAssemblyDef import MakeAssemblyDef
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef


def settings(*, drafting_standard, detail_flags, tessellation, system_preference_7a, journal_name):
    return ModelDefSettings(drafting_standard, tuple(detail_flags), tessellation, system_preference_7a,
                            journal_name, DOCUMENT_VERSION_2026)


def part_definition_graph(*, density_kg_m3, **presentation):
    return MakePartDef(settings(**presentation), density_kg_m3)


def assembly_definition_stream(*, save_as_part_preferences, **presentation):
    graph = MakeAssemblyDef(settings(**presentation), save_as_part_preferences)
    return WriteModelDef(graph).OutputValue
