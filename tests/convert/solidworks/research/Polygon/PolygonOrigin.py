from __future__ import annotations

# origin identity must survive a real container without marking ordinary vertices
KOrigin = """
OriginFeature = ModelFeature(
    cls='moOriginProfileFeature_c', name='Document origin', owner=Owner,
    allocator=Allocator, date_code=2026001, parasolid_version=380,
)
OriginFrame = PlaneFrame(origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0))
try:
    OriginProfile(profile=OriginFeature, plane=PlaneRef, frame=OriginFrame)
except ConstructionError:
    ReuseBlocked = True
else:
    raise RuntimeError('two profiles accepted the same exclusively owned plane wrapper')
OriginPlane = ComponentPlane(
    plane=Plane, component=UnitComponent(owner=Owner), created_at=1700000000,
    principal_normal=(0.0, 0.0, 1.0),
)
OriginGraph = OriginProfile(profile=OriginFeature, plane=OriginPlane, frame=OriginFrame)
"""
