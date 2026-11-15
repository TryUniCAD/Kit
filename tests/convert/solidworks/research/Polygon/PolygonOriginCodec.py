from __future__ import annotations

# native ownership and origin identity need verification after actual archive decoding
KOriginCodec = """
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
    'plane_reuse_blocked': ReuseBlocked, 'plane_wrappers_distinct': OriginPlane is not PlaneRef,
    'plane_owner_identity': OriginPlane['_profile_owner'] is OriginFeature and PlaneRef['_profile_owner'] is Profile.profile,
}
"""
