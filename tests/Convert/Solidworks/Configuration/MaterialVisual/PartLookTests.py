from io import BytesIO

from pytest import approx as ApproxValue
from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from tests.Convert.Solidworks.Configuration.MaterialVisual.RunVisualCase import (
    KVisualRoot,
)


# the native source distinguishes stored rendering data from physically assigned body materials
@MarkTests.parametrize("IncludeBrep", (True, False))
def TestPartLook(IncludeBrep: bool) -> None:
    Source = KVisualRoot / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"
    Default = OpenDocument(Source, include_brep=IncludeBrep)
    Document = OpenDocument(
        Source, include_brep=IncludeBrep, include_native_appearance=True
    )
    assert "solidworks.part_visual" not in Default.metadata
    Appearance = Document.metadata["solidworks.part_visual"]
    assert isinstance(Appearance, dict)
    Classic = Appearance["classic_renderer"]
    PbrView = Appearance["basic_pbr"]
    assert isinstance(Classic, dict) and isinstance(PbrView, dict)
    assert Appearance["model_rgb"] == Classic["primary_rgb"] == (228, 228, 228)
    assert Appearance["stored_label"] == "Steel"
    assert Appearance["record_end"] == 925
    assert Classic["roughness"] == ApproxValue(0.6)
    assert PbrView["roughness"] == ApproxValue(0.2)
    assert Appearance["primary_texture_wire"] is None
    assert Appearance["effective_body_appearance"] is None
    assert not Document.materials and all(
        not Body.material_id for Body in Document.bodies
    )
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored.metadata["solidworks.part_visual"] == Appearance
    assert not Restored.validate()


# publication must reject source appearance before either destination can be modified
def TestLookRefusal() -> None:
    Source = KVisualRoot / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"
    Document = OpenDocument(Source, include_native_appearance=True)
    Sink = BytesIO(b"existing destination")
    with RaisesError(ValueError, match="stored SOLIDWORKS part appearance"):
        WriteDocument(Document, Sink, destination_format="solidworks.sldprt")
    with RaisesError(ValueError, match="stored SOLIDWORKS part appearance"):
        SldprtWriter().write(Document, Sink)
    assert Sink.getvalue() == b"existing destination"
