from math import isclose as IsClose
from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from tests.Convert.Solidworks.Research.Cut.MakeThroughCutArchive import (
    MakeThroughCutArchive,
)


# symmetric stock can hide a mirrored cut in volume comparisons so the reconstructed rim positions need direct coverage
def TestColdThroughAllRims(TmpPath: FilePath) -> None:
    HalfDepth = 14.3 / 2.0
    for AxisValue, Reverse, Both, Heights in (
        ("z", True, False, (0.0, HalfDepth)),
        ("y", False, False, (-HalfDepth, 0.0)),
        ("x", True, True, (-HalfDepth, HalfDepth)),
    ):
        Payload = MakeThroughCutArchive(AxisValue, Reverse, Both)
        OutputPath = TmpPath / (AxisValue + ".SLDPRT")
        OutputPath.write_bytes(Payload)
        Document = OpenDoc(OutputPath)
        assert not Document.validate() and Document.brep_payloads == ()
        Brep = Document.brep
        (Body,) = Document.bodies
        assert Brep is not None and not Brep.validate(frozenset((Body.id,)))
        assert (len(Brep.faces), len(Brep.edges), len(Brep.vertices)) == (
            7 if Both else 8,
            14,
            10,
        )
        Rims = sorted(
            getattr(Curve.center, AxisValue)
            for Curve in Brep.curves
            if isinstance(Curve, CircleCurve)
        )
        assert all(
            IsClose(Rim, Height, rel_tol=0.0, abs_tol=1e-12)
            for Rim, Height in zip(Rims, Heights, strict=True)
        )
        (Cut,) = tuple(
            Feature
            for Feature in Document.feature_timeline
            if str(Feature.operation) == "cut"
        )
        Definition = Cut.definition
        assert isinstance(Definition, ExtrudeFeature)
        assert Definition.end_condition == ExtrudeEnd.KThroughAll
        assert Definition.reversed is Reverse and Definition.length is None
        assert Definition.second_end_condition == (
            ExtrudeEnd.KThroughAll if Both else None
        )
        assert Cut.parameter_ids == () and Body.final_feature_id == Cut.id
