from math import isclose as IsClose
from convert import open_document as OpenDoc


# strict public readback must expose a validated analytic body while preserving the complete editable profile and its active driver
def CheckPrismDoc(
    BytesValue: bytes, WidthValue: float, HeightValue: float, DepthValue: float
) -> None:
    DocumentValue = OpenDoc(BytesValue, source_format="solidworks.sldprt")
    assert DocumentValue.brep is not None and not DocumentValue.validate()
    assert DocumentValue.brep_payloads == () and DocumentValue.meshes == ()
    (BodyValue,) = DocumentValue.bodies
    GeometryValue = DocumentValue.brep
    assert (
        len(GeometryValue.vertices),
        len(GeometryValue.edges),
        len(GeometryValue.faces),
        len(GeometryValue.bodies),
    ) == (8, 12, 6, 1)
    TopologyValue = BodyValue.topology
    assert TopologyValue is not None
    VolumeValue, AreaValue = TopologyValue.volume, TopologyValue.surface_area
    assert VolumeValue is not None and AreaValue is not None
    assert IsClose(VolumeValue, WidthValue * HeightValue * DepthValue, rel_tol=1e-12)
    assert IsClose(
        AreaValue,
        2
        * (
            WidthValue * HeightValue
            + WidthValue * DepthValue
            + HeightValue * DepthValue
        ),
        rel_tol=1e-12,
    )
    assert all(Value.design_body_id == BodyValue.id for Value in GeometryValue.bodies)
    (SketchValue,) = DocumentValue.sketches
    assert (
        len(SketchValue.entities) == 4
        and len(SketchValue.closed_profile_entity_ids) == 1
    )
    BossValue = DocumentValue.feature_timeline[-1]
    assert (
        BossValue.sketch_id == SketchValue.id
        and BodyValue.final_feature_id == BossValue.id
    )
    Drivers = tuple(
        Value
        for Value in DocumentValue.parameters
        if Value.id in BossValue.parameter_ids
    )
    assert len(Drivers) == 1 and Drivers[0].owner_id == BossValue.id
    assert IsClose(float(Drivers[0].value.value), DepthValue, rel_tol=1e-12)
    NoTessValue = OpenDoc(
        BytesValue, source_format="solidworks.sldprt", include_tessellation=False
    )
    assert NoTessValue.brep == GeometryValue and NoTessValue.meshes == ()
    HistoryValue = OpenDoc(
        BytesValue, source_format="solidworks.sldprt", include_brep=False
    )
    assert HistoryValue.brep is None and HistoryValue.meshes == ()
    assert HistoryValue.feature_timeline == DocumentValue.feature_timeline
    assert (
        HistoryValue.sketches == DocumentValue.sketches
        and HistoryValue.parameters == DocumentValue.parameters
    )
