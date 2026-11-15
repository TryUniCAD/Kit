from __future__ import annotations

# origin identity must survive a real container without marking ordinary vertices
KOrigin = """
OriginFeature = ModelFeature(
    cls='moOriginProfileFeature_c', name='Document origin', owner=Owner,
    allocator=Allocator, date_code=2026001, parasolid_version=380,
)
OriginGraph = OriginProfile(
    profile=OriginFeature, plane=PlaneRef,
    frame=PlaneFrame(origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0)),
)
OriginSeed = ArchiveMap(2, {1: ('obj', OriginFeature)})
OriginContext = {'conditions': 0x2000, 'owner_is_drawing': 0, 'ctx874': 1}
OriginStore = Store(base=OriginSeed.count, registry=Registry, version=19000, ctx=OriginContext, seed=OriginSeed)
OriginStore.obj(OriginGraph.sketch)
OriginBytes = bytes(OriginStore.out)
OriginArchive = SldprtArchive.from_bytes(BuildContainer({'Research/Origin': OriginBytes}))
OriginLoad = Load(OriginArchive.require('Research/Origin'), base=OriginSeed.count, registry=Registry, version=19000, ctx=OriginContext, seed=OriginSeed)
OriginSketch = OriginLoad.obj()
if OriginLoad.left():
    raise RuntimeError('origin archive has unread bytes')
OriginPoint = OriginSketch['points'][0]['point']
OriginAgain = Store(base=OriginSeed.count, registry=Registry, version=19000, ctx=OriginContext, seed=OriginSeed)
OriginAgain.obj(OriginSketch)
if bytes(OriginAgain.out) != OriginBytes:
    raise RuntimeError('origin archive changed across the container boundary')
OriginReport = {
    'origin_flags': OriginPoint['pflags'], 'origin_type': OriginPoint['fe4'],
    'origin_relations': OriginSketch['dims']['nlog1'], 'origin_bytes': len(OriginBytes),
    'ordinary_origin_clear': all((Record['point']['pflags'] & 1) == 0 for Record in Profile.sketch['points']),
}
"""
