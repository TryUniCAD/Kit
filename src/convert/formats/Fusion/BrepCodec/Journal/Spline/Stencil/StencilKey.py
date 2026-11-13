from hashlib import sha256 as HashBytes

from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KWeightDigits = 12


def StencilKey(Surface: TsplineSurface) -> str:
    Header = Surface.Header
    Layout = (
        Header.Degree,
        Header.CapType,
        Header.StarSmoothness,
        Header.UnitScale,
        Header.EndConditions,
        Header.StarKnotRule,
        Header.Tolerance,
        Header.GeometryTol,
        Surface.Topology,
        Surface.Mapping,
        Surface.Creases,
        Surface.SmartGrips,
        tuple(round(GripValue.Weight, KWeightDigits) for GripValue in Surface.Grips),
    )
    return HashBytes(repr(Layout).encode("ascii")).hexdigest()
