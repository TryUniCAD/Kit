from dataclasses import replace as ReplaceValue

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.WithPartLook import WithPartLook
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepBody, BrepRegion
from tests.Convert.Solidworks.Configuration.MaterialVisual.RunVisualCase import (
    KVisualRoot,
)


# an unsupported appearance must not hide ambiguity already present in the imported geometry
def TestUnboundLook() -> None:
    Source = KVisualRoot / "re/solidworks/examples/.SLDPRT/example.SLDPRT"
    Document = OpenDocument(Source, include_brep=False)
    Archive = SldprtArchive.from_bytes(Source.read_bytes())
    Geometry = BrepModel(
        regions=(
            BrepRegion(id="first", shell_use_ids=()),
            BrepRegion(id="second", shell_use_ids=()),
        ),
        bodies=(BrepBody(id="carrier", region_ids=("first", "second")),),
    )
    Unbound = ReplaceValue(Document, brep=Geometry)
    assert WithPartLook(Unbound, Archive, 0, False) is Unbound
    Observed = WithPartLook(Unbound, Archive, 0, True)
    assert Observed.brep is Geometry
    assert tuple(
        Notice.code for Notice in Observed.diagnostics[len(Unbound.diagnostics) :]
    ) == (
        "solidworks.part_visual_unbound_regions",
        "solidworks.part_visual_unavailable",
    )
