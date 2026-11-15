from __future__ import annotations

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
