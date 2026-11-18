from math import isclose as IsClose
from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from tests.Convert.Solidworks.Research.Cut.MakePocketArchive import MakePocketArchive
from tests.Convert.Solidworks.Research.Cut.MakeThroughCutArchive import (
    MakeThroughCutArchive,
)


# symmetric stock can hide a mirrored cut in volume comparisons so the reconstructed rim positions need direct coverage
def TestColdThroughAllRims(TmpPath: FilePath) -> None:
    Source = MakePocketArchive(TmpPath / "Inputs")
    HalfDepth = 14.3 / 2.0
    for Reverse, Both, Heights in (
        (True, False, (0.0, HalfDepth)),
        (False, False, (-HalfDepth, 0.0)),
        (True, True, (-HalfDepth, HalfDepth)),
    ):
        Payload = MakeThroughCutArchive(Source, Reverse, Both)
        Document = OpenDoc(Payload, source_format="solidworks.sldprt")
        assert not Document.validate() and Document.brep_payloads == ()
        Brep = Document.brep
        (Body,) = Document.bodies
        assert Brep is not None and not Brep.validate(frozenset((Body.id,)))
        assert (len(Brep.faces), len(Brep.edges), len(Brep.vertices)) == (
            7 if Both else 8,
            14,
            10,
        )
        Rims = tuple(
            Curve.center.z for Curve in Brep.curves if isinstance(Curve, CircleCurve)
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
