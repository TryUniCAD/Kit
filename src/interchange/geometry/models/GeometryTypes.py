# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from functools import reduce as ReduceValues
from operator import or_ as UnionValues

from interchange.geometry.models.GeometryConics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)

# exhaustive geometry typing prevents new classes from escaping sketch validation
KGeometryTypes = ReduceValues(
    UnionValues,
    (
        PointGeometry,
        LineGeometry,
        CircleGeometry,
        ArcGeometry,
        EllipseGeometry,
        ArcEllipseGeom,
        HyperbolaGeom,
        ArcHyperGeom,
        ParabolaGeom,
        ArcParabGeom,
        SplineGeometry,
        NativeGeometry,
    ),
)
