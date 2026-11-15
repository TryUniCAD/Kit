from __future__ import annotations

# real archive behavior needs warmed components before runtime access is sealed
KLoad = """
from Core import ArchiveMap, Load, Obj, Store
from Classes import registry as GetRegistry
from builders.Model import PersistentIds, body_feature as BodyFeature
from builders.Model import component_plane as ComponentPlane
from builders.Model import model_feature as ModelFeature
from builders.Model import principal_plane as PrincipalPlane
from builders.Model import unit_component as UnitComponent
from builders.Sketch import ConstructionError, PlaneFrame
from builders.Sketch import closed_profile as ClosedProfile
from builders.Extrude import live_blind_extrusion as LiveBlindPad
from convert.adapters.solidworks.container.Container import build_sldprt as BuildContainer
from convert.adapters.solidworks.container.Container import SldprtArchive

Registry = GetRegistry()
Codecs = tuple(FindCodec(Name) for Name in ('utf-16-le', 'utf-8', 'latin-1'))
AuditValue.BeginBuild()
"""
