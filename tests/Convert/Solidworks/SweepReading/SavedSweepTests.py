from hashlib import sha256 as HashBytes
from io import BytesIO
from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Writing.CanWriteSweep import CanWriteSweep
from interchange.Features.SweepFeature import SweepFeature


# physical saved geometry and native driver ownership must agree in both read modes
def ReadSwFixture(Payload: bytes, Section: float, IncludeBrep: bool) -> None:
    Document = OpenDocument(
        Payload, source_format=KPartFormatId, strict=True, include_brep=IncludeBrep
    )
    (Feature,) = (
        RowValue
        for RowValue in Document.feature_timeline
        if isinstance(RowValue.definition, SweepFeature)
    )
    (BodyValue,) = Document.bodies
    Definition = Feature.definition
    assert isinstance(Definition, SweepFeature)
    Drivers = {
        Value.owner_id: Value.value.value
        for Value in Document.parameters
        if Value.name == "D1"
    }
    assert Drivers == {Feature.sketch_id: Section, Definition.PathSketchId: 41.297}
    assert set(Drivers) == {Sketch.id for Sketch in Document.sketches}
    assert BodyValue.final_feature_id == Feature.id
    assert Feature.OutputBodyIds == (BodyValue.id,)
    Topology = BodyValue.topology
    assert (
        Topology.solid_count,
        Topology.shell_count,
        Topology.face_count,
        Topology.edge_count,
        Topology.vertex_count,
    ) == (1, 1, 3, 2, 0)
    assert Document.source.attributes["saved_sweep_result"] is True
    assert (Document.brep is not None) is IncludeBrep
    assert not CanWriteSweep(Document, BytesIO())


# the independent section edit must survive strict native reads at exact parameter precision
def TestSavedSweep() -> None:
    Samples = (
        (
            "SweepArcWide.SLDPRT",
            11.426,
            "46a8faf1e54be5e312c0ab9f0e739c60cd4cd473bca09ae72369a552ef41675c",
        ),
        (
            "SweepArcWideSectionEdit.SLDPRT",
            14.186,
            "2e1db56ec1100add9c8f086a8a77d48e52bc573827972b194bde64261f5cfa37",
        ),
    )
    Fixtures = (
        FilePath(__file__).resolve().parents[4]
        / "re/solidworks/v2026/corpus/saved-sweep/SavedSweepWide01"
    )
    for NameValue, Section, Expected in Samples:
        Payload = (Fixtures / NameValue).read_bytes()
        assert HashBytes(Payload).hexdigest() == Expected
        for IncludeBrep in (True, False):
            ReadSwFixture(Payload, Section, IncludeBrep)
