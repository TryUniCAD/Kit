from math import isclose as IsClose
from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from tests.Convert.Solidworks.Research.Cut.MakeThroughCutArchive import (
    MakeThruArchive,
)


# symmetric stock can hide a mirrored cut in volume comparisons so the reconstructed rim positions need direct coverage
def TestThroughRims(TmpPath: FilePath) -> None:
    HalfDepth = 14.3 / 2.0
    for AxisValue, Reverse, BothEnds, Heights in (
        ("z", True, False, (0.0, HalfDepth)),
        ("y", False, False, (-HalfDepth, 0.0)),
        ("x", True, True, (-HalfDepth, HalfDepth)),
    ):
        Payload = MakeThruArchive(AxisValue, Reverse, BothEnds)
        OutputPath = TmpPath / (AxisValue + ".SLDPRT")
        _ = OutputPath.write_bytes(Payload)
        Document = OpenDoc(OutputPath)
        assert not Document.validate() and Document.brep_payloads == ()
        ModelBrep = Document.brep
        (BodyValue,) = Document.bodies
        assert ModelBrep is not None and not ModelBrep.validate(
            frozenset((BodyValue.id,))
        )
        assert (
            len(ModelBrep.faces),
            len(ModelBrep.edges),
            len(ModelBrep.vertices),
        ) == (
            7 if BothEnds else 8,
            14,
            10,
        )
        RimPositions = sorted(
            getattr(Curve.center, AxisValue)
            for Curve in ModelBrep.curves
            if isinstance(Curve, CircleCurve)
        )
        assert all(
            IsClose(RimPosition, Height, rel_tol=0.0, abs_tol=1e-12)
            for RimPosition, Height in zip(RimPositions, Heights, strict=True)
        )
        (CutFeature,) = tuple(
            Feature
            for Feature in Document.feature_timeline
            if str(Feature.operation) == "cut"
        )
        Definition = CutFeature.definition
        assert isinstance(Definition, ExtrudeFeature)
        assert Definition.end_condition == ExtrudeEnd.KThroughAll
        assert Definition.reversed is Reverse and Definition.length is None
        assert Definition.second_end_condition == (
            ExtrudeEnd.KThroughAll if BothEnds else None
        )
        assert (
            CutFeature.parameter_ids == ()
            and BodyValue.final_feature_id == CutFeature.id
        )
