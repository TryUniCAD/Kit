from __future__ import annotations

# native origin identity and pending state must survive complete profile serialization
KOriginCodec = """
OriginSeed = ArchiveMap(2, {1: ('obj', Owner)})
OriginContext = {'conditions': 0x2000, 'owner_is_drawing': 0, 'ctx874': 1}
OriginStore = Store(base=OriginSeed.count, registry=Registry, version=19000, ctx=OriginContext, seed=OriginSeed)
OriginStore.obj(OriginGraph.profile)
OriginBytes = bytes(OriginStore.out)
OriginArchive = SldprtArchive.from_bytes(BuildContainer({'Research/Origin': OriginBytes}))
OriginLoad = Load(OriginArchive.require('Research/Origin'), base=OriginSeed.count, registry=Registry, version=19000, ctx=OriginContext, seed=OriginSeed)
OriginNode = OriginLoad.obj()
OriginSketch = OriginNode['pd_f80']
if OriginLoad.left():
    raise RuntimeError('origin archive has unread bytes')
if OriginSketch['f138'] is not OriginNode:
    raise RuntimeError('origin sketch lost its actual profile owner')
OriginPoint = OriginSketch['points'][0]['point']
OriginAgain = Store(base=OriginSeed.count, registry=Registry, version=19000, ctx=OriginContext, seed=OriginSeed)
OriginAgain.obj(OriginNode)
if bytes(OriginAgain.out) != OriginBytes:
    raise RuntimeError('origin archive changed across the container boundary')
"""
