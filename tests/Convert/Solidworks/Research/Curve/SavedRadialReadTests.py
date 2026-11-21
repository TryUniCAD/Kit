from math import isclose as IsClose
from typing import cast as CastValue

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# native edited circles must retain an actual closed boundary and both driving references
def TestRadialRead() -> None:
    CorpusPath = KRepoRoot / "re/solidworks/v2026/corpus/circle-saves"
    for NameValue, KindValue, Multiplier in (
        ("CircleRadiusBoss", "radius", 1),
        ("CircleDiameterBoss", "diameter", 2),
    ):
        SourcePath = CorpusPath / f"{NameValue}-edited-fresh-reopen.SLDPRT"
        Payload = SourcePath.read_bytes()
        ArchiveValue = SldprtArchive.from_bytes(Payload)
        Linked = ReadNativeLink(ArchiveValue, 0)
        Resolved = Linked.ResolvedValue
        Output, ModelValue = WriteResolMut(
            Resolved.RootsValue,
            Resolved.ExtraFields,
            Resolved.VersionValue,
            Linked.ConfigValue.MapValue,
            Resolved.ContextValue,
        )
        assert Output == ArchiveValue.require(Linked.StreamName)
        assert Resolved.MapValue == ModelValue.MapValue
        Document = OpenDocument(
            SourcePath, include_brep=False, include_tessellation=False
        )
        Metadata = CastValue(
            dict[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
        )
        assert Metadata["typed_geometry_projection"] is True
        (Sketch,) = Document.sketches
        (Circle,) = (
            Entity
            for Entity in Sketch.entities
            if isinstance(Entity.geometry, CircleGeometry)
        )
        (Point,) = (
            Entity
            for Entity in Sketch.entities
            if isinstance(Entity.geometry, PointGeometry)
        )
        assert isinstance(Circle.geometry, CircleGeometry)
        assert isinstance(Point.geometry, PointGeometry)
        assert not Circle.construction and Sketch.closed_profile_entity_ids == (
            (Circle.id,),
        )
        assert Point.geometry.point == Circle.geometry.center
        Radial, Fixed = Sketch.constraints
        assert Radial.kind == KindValue and Radial.driving
        assert tuple(Reference.entity_id for Reference in Radial.references) == (
            Circle.id,
        )
        assert Fixed.kind == "fixed"
        assert tuple(Reference.entity_id for Reference in Fixed.references) == (
            Point.id,
        )
        Parameter = Document.parameter(CastValue(str, Radial.parameter_id))
        assert Parameter.value.unit == "mm"
        assert IsClose(
            CastValue(float, Parameter.value.value),
            Multiplier * Circle.geometry.radius,
            rel_tol=2e-6,
        )
        assert SourcePath.read_bytes() == Payload
