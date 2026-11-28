from convert import open_document as OpenDocument
from tests.Convert.Solidworks.Configuration.MaterialVisual.RunVisualCase import (
    KVisualRoot,
)


# a native part with multiple regions must preserve its geometry even when appearance is unavailable
def TestUnboundLook() -> None:
    Source = (
        KVisualRoot
        / "re/solidworks/examples"
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "RODAMIENTO DE BANDA.SLDPRT"
    )
    Default = OpenDocument(Source)
    Observed = OpenDocument(Source, include_native_appearance=True)
    assert Default.brep is not None
    SolidIds = {Region.id for Region in Default.brep.regions if Region.solid}
    assert any(
        not Carrier.design_body_id
        and len(SolidIds.intersection(Carrier.region_ids)) >= 2
        for Carrier in Default.brep.bodies
    )
    assert Observed.brep == Default.brep
    assert Observed.bodies == Default.bodies
    assert Observed.diagnostics[: len(Default.diagnostics)] == Default.diagnostics
    assert tuple(
        Notice.code for Notice in Observed.diagnostics[len(Default.diagnostics) :]
    ) == (
        "solidworks.part_visual_unbound_regions",
        "solidworks.part_visual_unavailable",
    )
