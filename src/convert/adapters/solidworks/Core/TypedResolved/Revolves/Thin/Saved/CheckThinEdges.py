from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadThinTrim import (
    ReadThinTrim,
)
from interchange.brep.Topology.BrepModel import BrepModel


# mapped edge uses preserve curve type and the real bounded span on that carrier
def CheckThinEdges(
    Actual: BrepModel, Expected: BrepModel, PointsValue: Mapping[str, str]
) -> dict[str, str]:
    EdgesValue = {
        frozenset((EdgeValue.start_vertex_id, EdgeValue.end_vertex_id)): EdgeValue
        for EdgeValue in Expected.edges
    }
    CurvesValue = {Curve.id: Curve for Curve in Actual.curves}
    TargetCurves = {Curve.id: Curve for Curve in Expected.curves}
    Matched: dict[str, str] = {}
    for EdgeValue in Actual.edges:
        PairValue = frozenset(
            (
                PointsValue[EdgeValue.start_vertex_id],
                PointsValue[EdgeValue.end_vertex_id],
            )
        )
        Target = EdgesValue[PairValue]
        CurveValue, TargetCurve = (
            CurvesValue[EdgeValue.curve_id],
            TargetCurves[Target.curve_id],
        )
        TrimValue = abs(EdgeValue.end_parameter - EdgeValue.start_parameter)
        TargetTrim = abs(Target.end_parameter - Target.start_parameter)
        Middle = ReadThinTrim(
            CurveValue, (EdgeValue.start_parameter + EdgeValue.end_parameter) / 2
        )
        TargetMid = ReadThinTrim(
            TargetCurve, (Target.start_parameter + Target.end_parameter) / 2
        )
        if (
            type(CurveValue) is not type(TargetCurve)
            or not IsClose(TrimValue, TargetTrim, rel_tol=1e-12, abs_tol=1e-9)
            or any(
                not IsClose(LeftValue, RightValue, rel_tol=1e-12, abs_tol=1e-9)
                for LeftValue, RightValue in zip(Middle, TargetMid, strict=True)
            )
        ):
            raise ValueError("SOLIDWORKS thin cache edge has an unresolved sector trim")
        Matched[EdgeValue.id] = Target.id
    if len(Matched) != len(EdgesValue) or len(set(Matched.values())) != len(Matched):
        raise ValueError("SOLIDWORKS thin cache has incomplete sector edge ownership")
    return Matched
