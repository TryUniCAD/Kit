from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

KRepoRoot = FilePath(__file__).resolve().parents[4]
KImports = """
import json
import sys
from math import cos, sin, tau
from pathlib import Path

RepoRoot = Path(sys.argv[1])
Scenario = sys.argv[2]
Count = int(sys.argv[3])
Depth = float(sys.argv[4])
sys.dont_write_bytecode = True
sys.path.insert(0, str(RepoRoot / 'src'))
sys.path.insert(0, str(RepoRoot / 're' / 'tooling' / 'sw2026'))
sys.path.insert(0, str(RepoRoot / 're' / 'tooling' / 'sw2026' / 'serial'))

from Core import ArchiveMap, Load, Obj, Store
from Classes import registry
from builders.Model import PersistentIds, body_feature, component_plane
from builders.Model import model_feature, principal_plane, unit_component
from builders.Sketch import ConstructionError, PlaneFrame, closed_profile
from builders.Extrude import live_blind_extrusion
from convert.adapters.solidworks.container.Container import build_sldprt, SldprtArchive

Registry = registry()
"""

KGuard = """
Reads = []

def Audit(Event, Args):
    if Event in {'subprocess.Popen', 'os.system'}:
        raise RuntimeError('fresh construction launched an external process')
    if Event != 'open':
        return
    Name, Mode, Flags = Args
    if not isinstance(Name, (str, bytes)):
        return
    Name = Name.decode() if isinstance(Name, bytes) else Name
    if Path(Name).suffix in {'.py', '.pyc', '.so', '.dylib'}:
        return
    Reads.append(Name)
    raise RuntimeError('runtime file access during fresh construction: ' + Name)

sys.addaudithook(Audit)
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
    Vertices = tuple((cos(tau * Index / Count), sin(tau * Index / Count)) for Index in range(Count))
Allocator = PersistentIds()
Owner = Obj('moPart_c')
Plane = principal_plane(
    axis='z', name='Authored plane', owner=Owner, allocator=Allocator,
    date_code=2026001, parasolid_version=380, retain_construction_flag=True,
)
PlaneRef = component_plane(
    plane=Plane, component=unit_component(owner=Owner), created_at=1700000000,
    principal_normal=(0.0, 0.0, 1.0),
)
Profile = model_feature(
    cls='moProfileFeature_c', name='Authored sketch', owner=Owner,
    allocator=Allocator, date_code=2026001, parasolid_version=380,
)
try:
    Profile = closed_profile(
        vertices=Vertices, profile=Profile, plane=PlaneRef,
        frame=PlaneFrame(origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0)),
    )
except ConstructionError as Error:
    print(json.dumps({'rejected': str(Error), 'runtime_reads': Reads}))
    raise SystemExit(2)
Feature = body_feature(
    cls='moExtrusion_c', name='Authored pad', owner=Owner,
    allocator=Allocator, date_code=2026001, parasolid_version=380,
)
FirstDimId = Allocator.next_id
Graph = live_blind_extrusion(
    feature=Feature, profile=Profile, depth=Depth, allocator=Allocator,
    design_intent=False, selected_leader=0,
)
"""

KCodec = """
Seed = ArchiveMap(2, {1: ('obj', Profile.profile)})
Context = {'conditions': 0x2000, 'owner_is_drawing': 0}
SketchStore = Store(base=Seed.count, registry=Registry, version=19000, ctx=Context, seed=Seed)
SketchStore.obj(Profile.sketch)
EndStore = Store(registry=Registry, version=19000, ctx=Context)
EndStore.obj(Graph.end_spec)
Streams = {'Research/Sketch': bytes(SketchStore.out), 'Research/BlindEnd': bytes(EndStore.out)}
Container = build_sldprt(Streams)
Archive = SldprtArchive.from_bytes(Container)
SketchLoad = Load(Archive.require('Research/Sketch'), base=Seed.count, registry=Registry, version=19000, ctx=Context, seed=Seed)
Sketch = SketchLoad.obj()
EndLoad = Load(Archive.require('Research/BlindEnd'), registry=Registry, version=19000, ctx=Context)
End = EndLoad.obj()
if SketchLoad.left() or EndLoad.left():
    raise RuntimeError('fresh graph archive has unread bytes')
SketchAgain = Store(base=Seed.count, registry=Registry, version=19000, ctx=Context, seed=Seed)
SketchAgain.obj(Sketch)
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
    'dimension_refcounts': [Dimension['refcount'] for Dimension in Dimensions],
    'distinct_displays': len({id(Display) for Display in Displays}),
    'distinct_handles': len({id(Handle) for Handle in Handles}),
    'distinct_parameters': len({id(Parameter) for Parameter in Parameters}),
    'edited_depth': Edited['f18']['f850'][0]['o']['ff0']['f28']['f58'],
    'reverse_depth': Edited['f20']['f850'][0]['o']['ff0']['f28']['f58'],
    'stream_bytes': {Name: len(Data) for Name, Data in Streams.items()},
    'container_bytes': len(Container), 'runtime_reads': Reads,
    'vendor_loadable': False, 'application_usable': False,
}
print(json.dumps(Report))
"""

KProgram = KImports + KGuard + KInput + KCodec + KReport


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
