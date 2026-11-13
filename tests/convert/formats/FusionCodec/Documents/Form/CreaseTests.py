from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import (
    SpreadKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import (
    ConvertForm,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import (
    CageBody,
    ShapeBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    CurveFrame,
    SurfaceFrame,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapFormCage import (
    SwapFormCage,
)
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.CreaseFiles import (
    KCreaseBent,
    KCreaseCarrier,
    KCreaseOracle,
    KCreaseSplit,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ReadConverted,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

KFrameSlack = 1e-12
KFrameKnots = ((0.0, 3), (0.25, 2), (1.0, 1), (1.75, 2), (2.0, 3))
KFrameParams = (0.0, 0.1, 0.25, 0.6, 1.0, 1.3, 1.75, 1.9, 2.0)
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)


def SpreadOrder(Knots: tuple[tuple[float, int], ...]) -> list[float]:
    return SpreadKnots(
        tuple(KnotValue for KnotValue, _ in Knots),
        tuple(Count for _, Count in Knots),
    )


def Greville(Knots: tuple[tuple[float, int], ...]) -> list[float]:
    Spread = SpreadOrder(Knots)
    return [
        sum(Spread[Index + 1 : Index + 4]) / 3.0 for Index in range(len(Spread) - 4)
    ]


def TestCurveFrame() -> None:
    Places = Greville(KFrameKnots)
    Curve = BsCurve(
        False,
        3,
        0,
        tuple(KnotValue for KnotValue, _ in KFrameKnots),
        tuple(Count for _, Count in KFrameKnots),
        2,
        tuple((Place, 5.0) for Place in Places),
        (),
    )
    for Param in KFrameParams:
        Point, Tangent = CurveFrame(Curve, Param)
        assert abs(Point[0] - Param) <= KFrameSlack
        assert abs(Point[1] - 5.0) <= KFrameSlack
        assert abs(Tangent[0] - 1.0) <= KFrameSlack
        assert abs(Tangent[1]) <= KFrameSlack


def TestSurfaceAxes() -> None:
    Places = Greville(KFrameKnots)
    Knots = tuple(SplineKnot(KnotValue, Count) for KnotValue, Count in KFrameKnots)
    Points = tuple(
        (PlaceU, PlaceV, PlaceU * PlaceV) for PlaceV in Places for PlaceU in Places
    )
    Surface = NubsSurface(3, 3, 0, 0, 0, 0, Knots, Knots, Points)
    for ParamU in KFrameParams:
        for ParamV in KFrameParams:
            AlongU, AlongV = SurfaceFrame(Surface, ParamU, ParamV)
            Expected = ((1.0, 0.0, ParamV), (0.0, 1.0, ParamU))
            for Found, Wanted in zip((AlongU, AlongV), Expected, strict=True):
                assert max(
                    abs(First - Second) for First, Second in zip(Found, Wanted)
                ) <= (KFrameSlack)


@KNeedZip
def TestCreaseClass() -> None:
    Carrier = ReadDocument(ReadFormFile(*KCreaseCarrier)).Forms[0].Surface
    assert CageBody(Carrier) == ShapeBody(Carrier)
    BentCage = ReadTspline(ReadFormFile(*KCreaseBent))
    Shaped = [EdgeValue.Convexity for EdgeValue in ShapeBody(BentCage).Edges]
    Classes = [EdgeValue.Convexity for EdgeValue in CageBody(BentCage).Edges]
    assert Shaped.count("unknown") + 1 == Classes.count("unknown")
    Oracle = ReadConverted(ReadDocument(ReadFormFile(*KCreaseOracle)))
    assert [EdgeValue.Convexity for EdgeValue in Oracle.Edges] == Classes


@KNeedZip
def TestCreaseFault() -> None:
    Model = ReadDocument(ReadFormFile(*KCreaseCarrier))
    Split = ReadDocument(ReadFormFile(*KCreaseSplit)).Forms[0].Surface
    with RaisesError(ValueError, match="may split or reclassify"):
        _ = CageBody(Split)
    with RaisesError(ValueError, match="may split or reclassify"):
        _ = ConvertForm(Split)
    with RaisesError(ValueError, match="may split or reclassify"):
        _ = SwapFormCage(Model, Split)
    BentCage = ReadTspline(ReadFormFile(*KCreaseBent))
    with RaisesError(ValueError, match="change a crease edge class"):
        _ = SwapFormCage(Model, BentCage)
