from math import pi as PiValue
from ntpath import basename as BaseName, splitext as SplitExt
from sys import float_info as FloatInfo

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Container.Format import KPartSuffix
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# canonical sweep compilation may use only explicit valid model geometry and part identity
def CheckSweepInput(
    NameValue: str,
    SectionValue: CircleGeometry,
    PathValue: ArcGeometry,
    DensityValue: float,
    OutputValue: SelfFileInput,
) -> None:
    if type(OutputValue) is not SelfFileInput or not ReadStyleText(
        NameValue, "sweep part name"
    ):
        raise ValueError("sweep requires an explicit native part identity")
    StemValue, Extension = SplitExt(BaseName(OutputValue.PathName))
    if StemValue != NameValue or Extension.casefold() != KPartSuffix:
        raise ValueError("sweep part name must match its native part locator")
    if type(SectionValue) is not CircleGeometry or type(PathValue) is not ArcGeometry:
        raise ValueError("sweep requires one exact circle and one exact arc")
    if not all(
        type(Value) in (int, float)
        for Value in (SectionValue.Radius, PathValue.Radius, DensityValue)
    ) or not (
        0.001 <= SectionValue.Radius < PathValue.Radius <= 0.15
        and 0 < DensityValue <= FloatInfo.max
    ):
        raise ValueError(
            "sweep requires separated measured radii and positive finite density"
        )
    if (
        SectionValue.Center != PlaneVector(0.0, 0.0)
        or PathValue.Center != PlaneVector(0.0, PathValue.Radius)
        or type(PathValue.StartAngle) not in (int, float)
        or type(PathValue.EndAngle) not in (int, float)
        or (PathValue.StartAngle, PathValue.EndAngle) != (-PiValue / 2, 0.0)
    ):
        raise ValueError(
            "sweep requires an origin centred right section and positive origin start front quarter arc"
        )
