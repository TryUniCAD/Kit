from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

KRepoRoot = FilePath(__file__).resolve().parents[4]
KPaths = """
import sys as SysValue
from codecs import lookup as FindCodec
from json import dumps as DumpJson
from math import cos as CosValue, sin as SinValue, tau as TauValue
from pathlib import Path as FilePath

RepoRoot = FilePath(SysValue.argv[1])
Scenario = SysValue.argv[2]
Count = int(SysValue.argv[3])
Depth = float(SysValue.argv[4])
SysValue.dont_write_bytecode = True
SysValue.path.insert(0, str(RepoRoot))
SysValue.path.insert(0, str(RepoRoot / 'src'))
SysValue.path.insert(0, str(RepoRoot / 're' / 'tooling' / 'sw2026'))
SysValue.path.insert(0, str(RepoRoot / 're' / 'tooling' / 'sw2026' / 'serial'))

from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

AuditValue = BuildAudit(RepoRoot / 're' / 'tooling' / 'sw2026' / 'serial' / 'defs')
SysValue.addaudithook(AuditValue.InspectEvent)
"""

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

KInput = """
Cases = {
    'crossing': ((0, 0), (3, 2), (0, 3), (2, 0)),
    'touch': ((0, 0), (3, 0), (3, 3), (1, 0), (0, 3)),
    'vertical_overlap': ((0, 0), (0, 4), (3, 4), (0, 1), (0, 3), (3, 0)),
    'backtrack': ((0, 0), (3, 0), (1, 0), (3, 3), (0, 3)),
    'collinear': ((0, 0), (1, 0), (3, 0), (3, 2), (0, 2)),
    'vertical': ((0, 0), (3, 0), (3, 1), (3, 3), (0, 3), (0, 2)),
}
Vertices = Cases.get(Scenario)
if Vertices is None:
    Vertices = tuple((CosValue(TauValue * Index / Count), SinValue(TauValue * Index / Count)) for Index in range(Count))
"""

KSketch = """
Allocator = PersistentIds()
Owner = Obj('moPart_c')
Plane = PrincipalPlane(
    axis='z', name='Authored plane', owner=Owner, allocator=Allocator,
    date_code=2026001, parasolid_version=380, retain_construction_flag=True,
)
PlaneRef = ComponentPlane(
    plane=Plane, component=UnitComponent(owner=Owner), created_at=1700000000,
    principal_normal=(0.0, 0.0, 1.0),
)
Profile = ModelFeature(
    cls='moProfileFeature_c', name='Authored sketch', owner=Owner,
    allocator=Allocator, date_code=2026001, parasolid_version=380,
)
try:
    Profile = ClosedProfile(
        vertices=Vertices, profile=Profile, plane=PlaneRef,
        frame=PlaneFrame(origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0)),
    )
except ConstructionError as Error:
    print(DumpJson({'rejected': str(Error), 'runtime_reads': AuditValue.DeniedReads}))
    raise SystemExit(2)
"""

KFeature = """
Feature = BodyFeature(
    cls='moExtrusion_c', name='Authored pad', owner=Owner,
    allocator=Allocator, date_code=2026001, parasolid_version=380,
)
FirstDimId = Allocator.next_id
Graph = LiveBlindPad(
    feature=Feature, profile=Profile, depth=Depth, allocator=Allocator,
    design_intent=False, selected_leader=0,
)
"""

KEncode = """
Seed = ArchiveMap(2, {1: ('obj', Profile.profile)})
Context = {'conditions': 0x2000, 'owner_is_drawing': 0, 'ctx874': 1}
SketchStore = Store(base=Seed.count, registry=Registry, version=19000, ctx=Context, seed=Seed)
SketchStore.obj(Profile.sketch)
LateOffset = len(SketchStore.out)
SketchStore.obj(Profile.sketch['_point_nodes'][-1]['h2'])
LateBytes = bytes(SketchStore.out[LateOffset:])
EndStore = Store(registry=Registry, version=19000, ctx=Context)
EndStore.obj(Graph.end_spec)
Streams = {'Research/Sketch': bytes(SketchStore.out), 'Research/BlindEnd': bytes(EndStore.out)}
Container = BuildContainer(Streams)
Archive = SldprtArchive.from_bytes(Container)
"""

KDecode = """
SketchLoad = Load(Archive.require('Research/Sketch'), base=Seed.count, registry=Registry, version=19000, ctx=Context, seed=Seed)
Sketch = SketchLoad.obj()
LateHandle = SketchLoad.obj()
if LateHandle is not Sketch['points'][-1]['point']['h2']:
    raise RuntimeError('late archive handle reference identity was lost')
EndLoad = Load(Archive.require('Research/BlindEnd'), registry=Registry, version=19000, ctx=Context)
End = EndLoad.obj()
if SketchLoad.left() or EndLoad.left():
    raise RuntimeError('fresh graph archive has unread bytes')
SketchAgain = Store(base=Seed.count, registry=Registry, version=19000, ctx=Context, seed=Seed)
SketchAgain.obj(Sketch)
SketchAgain.obj(LateHandle)
EndAgain = Store(registry=Registry, version=19000, ctx=Context)
EndAgain.obj(End)
if bytes(SketchAgain.out) != Streams['Research/Sketch'] or bytes(EndAgain.out) != Streams['Research/BlindEnd']:
    raise RuntimeError('fresh graph changed across its binary archive boundary')
if Sketch['f138'] is not Profile.profile:
    raise RuntimeError('seeded profile owner identity was lost')
Displays = [End[Name] for Name in ('f18', 'f20', 'fc8', 'fd0')]
Handles = [Display['f850'][0]['o'] for Display in Displays]
Dimensions = [Handle['ff0'] for Handle in Handles]
Parameters = [Dimension['f28'] for Dimension in Dimensions]
"""

KRefs = """
PointRefs = []
for Index, Entry in enumerate(Sketch['points']):
    Point = Entry['point']
    First = Point['h1']['idx'] if Point['h1']['idx'] < 0x777f else Point['h1']['f18']
    Second = Point['h2']['idx'] if Point['h2']['idx'] < 0x777f else Point['h2']['f18']
    Expected = (0, len(Vertices) - 1) if Index == 0 else (Index - 1, Index)
    PointRefs.append((First, Second) == Expected and Point['fe8'] == 2)
LineRefs = []
for Index, Entry in enumerate(Sketch['lines']):
    Line = Entry['line']
    Start = Line['fc8_s'] if Line['fc8_s'] < 0xffff else Line['fc8']
    Finish = Line['fcc_s'] if Line['fcc_s'] < 0xffff else Line['fcc']
    LineRefs.append((Start, Finish) == (Index, (Index + 1) % len(Vertices)))
Parameters[0]['f58'] = Depth * 1.75
EditedStore = Store(registry=Registry, version=19000, ctx=Context)
EditedStore.obj(End)
EditedLoad = Load(bytes(EditedStore.out), registry=Registry, version=19000, ctx=Context)
Edited = EditedLoad.obj()
"""

KReport = """
Report = {
    'point_count': Sketch['npoints'], 'line_count': Sketch['nlines'],
    'point_references': all(PointRefs), 'line_references': all(LineRefs),
    'point_creation_next': Sketch['f140']['f08'],
    'line_creation_next': Sketch['f140']['f0c'], 'marker_next': Sketch['f130'],
    'parameter_names': [Parameter['f18']['f08'] for Parameter in Parameters],
    'parameter_ids': [Parameter['f08'] for Parameter in Parameters],
    'dimension_ids': [Dimension['f50'] for Dimension in Dimensions],
    'expected_first_dimension_id': FirstDimId,
    'next_persistent_id': Allocator.next_id,
    'from_offset_id': Graph.from_offset.dimension['f50'],
    'from_offset_name': Graph.from_offset.parameter['f18']['f08'],
    'constructed_dimensions': len(Graph.constructed_dimensions),
    'dimension_refcounts': [Dimension['refcount'] for Dimension in Dimensions],
    'distinct_displays': len({id(Display) for Display in Displays}),
    'distinct_handles': len({id(Handle) for Handle in Handles}),
    'distinct_parameters': len({id(Parameter) for Parameter in Parameters}),
    'edited_depth': Edited['f18']['f850'][0]['o']['ff0']['f28']['f58'],
    'reverse_depth': Edited['f20']['f850'][0]['o']['ff0']['f28']['f58'],
    'stream_bytes': {Name: len(Data) for Name, Data in Streams.items()},
    'container_bytes': len(Container), 'runtime_reads': AuditValue.DeniedReads,
    'module_read_count': len(AuditValue.ModuleReads),
    'vendor_loadable': False, 'application_usable': False,
}
"""

KWidths = """
Report['last_reference_tags'] = [Point['h2']['idx'], Line['fc8_s']]
Report['last_reference_indices'] = [Second, Start]
Report['late_reference_tag'] = int.from_bytes(LateBytes[:2], 'little')
Report['late_reference_bytes'] = len(LateBytes)
print(DumpJson(Report))
"""

KProgram = (
    KPaths
    + KLoad
    + KInput
    + KSketch
    + KFeature
    + KEncode
    + KDecode
    + KRefs
    + KReport
    + KWidths
)


def RunPolygon(
    *, Directory: FilePath, Scenario: str, Count: int, Depth: float
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-c",
            KProgram,
            str(KRepoRoot),
            Scenario,
            str(Count),
            str(Depth),
        ],
        cwd=Directory,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
