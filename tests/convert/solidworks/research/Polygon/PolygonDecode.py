from __future__ import annotations

# independent decoding prevents emitted byte identity from hiding broken links
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
