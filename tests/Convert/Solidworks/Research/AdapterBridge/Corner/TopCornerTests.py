from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from unittest.mock import patch as Patch

from pytest import raises as Raises

from convert import open_document as OpenDoc
from convert import write_document as WriteDoc
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import (
    LowerBoxModel,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# a reversed boss must retain its fixed corner and refuse the same coordinates with the anchor absent
def TestTopOrigin(TmpPath: FilePath) -> None:
    SeedValue = MakePlainDoc("SignedBox", 21.0, 28.0, 13.0)
    SeedValue = Replace(
        SeedValue,
        configurations=(Replace(SeedValue.configurations[0], name="Default"),),
        support_planes=(
            Replace(
                SeedValue.support_planes[0],
                name="XZ-plane",
                transform=Transform(
                    SpaceVector(0, 0, 0),
                    SpaceVector(1, 0, 0),
                    SpaceVector(0, 0, -1),
                    SpaceVector(0, 1, 0),
                ),
            ),
        ),
    )
    Unanchored = LowerBoxModel(
        SeedValue,
        "SignedBox",
        ("dimension/length", "dimension/width", "dimension/depth"),
        (21.0, 28.0, 13.0),
        ("Length", "Width", "Height"),
        "Named Body",
        TopAttached=True,
    )
    (Profile,) = Unanchored.sketches
    Datum = SketchEntity(
        "point/origin",
        GeometryKind.KPoint,
        PointGeometry(PlaneVector(0, 0)),
        construction=True,
        fixed=True,
    )
    Constraint = SketchRelation(
        "relation/origin",
        "coincident",
        (ConstraintRef(Datum.id), ConstraintRef(Profile.entities[0].id, "start")),
    )
    Anchored = Replace(
        Unanchored,
        sketches=(
            Replace(
                Profile,
                entities=(*Profile.entities, Datum),
                constraints=(*Profile.constraints, Constraint),
            ),
        ),
    )
    PathValue = TmpPath / "SignedBox.SLDPRT"
    with Raises((ValueError, AdapterNotFoundError)):
        _ = WriteDoc(Unanchored, PathValue, allow_carrier=False)
    assert not PathValue.exists()

    Stream = BytesIO()
    Policy = {"require_native_transfers": True}
    with Patch(
        "convert.adapters.solidworks.Core.Writing.EmitNativeMut.ReadTime",
        return_value=1795128000,
    ):
        Output = WriteDoc(Anchored, PathValue, allow_carrier=False, values=Policy)
        StreamResult = WriteDoc(
            Anchored,
            Stream,
            destination_format="solidworks.sldprt",
            allow_carrier=False,
            values={**Policy, "final_destination": str(PathValue)},
        )
    assert Output.bytes_written == StreamResult.bytes_written == len(Stream.getvalue())
    assert PathValue.read_bytes() == Stream.getvalue()
    assert Anchored.capabilities <= Output.native_capabilities and not Output.dropped

    Parsed = OpenDoc(PathValue, strict=True)
    Sketch = Parsed.sketches[0]
    (Plane,) = (
        Plane for Plane in Parsed.support_planes if Plane.id == Sketch.support_plane_id
    )
    (Operation,) = (
        RowValue.definition
        for RowValue in Parsed.feature_timeline
        if isinstance(RowValue.definition, ExtrudeFeature)
    )
    assert Plane.name == "Top Plane" and Operation.reversed
    assert [
        (BodyValue.name, BodyValue.topology.solid_count) for BodyValue in Parsed.bodies
    ] == [("Named Body", 1)]
    assert {
        Parameter.name: Parameter.value.value for Parameter in Parsed.parameters
    } == {
        "Length": 21.0,
        "Width": 28.0,
        "Height": 13.0,
    }
    assert (
        sum(
            RuleValue.kind == "coincident" and RuleValue.driving
            for RuleValue in Sketch.constraints
        )
        == 1
    )
