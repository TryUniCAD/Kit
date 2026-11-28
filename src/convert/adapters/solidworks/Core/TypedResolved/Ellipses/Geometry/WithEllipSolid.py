from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar

from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    EllipPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.Geometry.BuildEllipShell import (
    BuildEllipShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.Geometry.EllipMeasures import (
    EllipMeasures,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# the same measured live profile supplies the analytic boundary and uniform solid properties
def WithEllipSolid(DocumentValue: CadDocument, PartValue: EllipPartRead) -> CadDocument:
    (BodyValue,) = DocumentValue.bodies
    Driver = PartValue.BossValue.DepthValue.DepthValue
    DepthMm = RequireScalar(Driver.value_mm)
    Ellipse = PartValue.GeometryValue
    ModelValue = BuildEllipShell(Ellipse, DepthMm, BodyValue.id)
    BodyValue = ReplaceValue(
        BodyValue,
        topology=EllipMeasures(Ellipse, DepthMm, ModelValue),
        attributes=FreezeMapping(
            {
                **BodyValue.attributes,
                "solidworks.body_centroid_mm": (
                    Ellipse.center.x,
                    Ellipse.center.y,
                    DepthMm / 2,
                ),
            }
        ),
    )
    return ReplaceValue(DocumentValue, bodies=(BodyValue,), brep=ModelValue)
