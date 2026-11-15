from __future__ import annotations

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
