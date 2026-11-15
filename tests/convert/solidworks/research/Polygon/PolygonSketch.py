from __future__ import annotations

# semantic vertices need a fresh graph before archive behavior is meaningful
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
