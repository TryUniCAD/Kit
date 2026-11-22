from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Ellipse.PlanEllipse import PlanEllipse
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipAxisGeom import (
    EllipAxisGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    KEllipseStations,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch


# cold semantic input uses the projected conic while retaining its identities for later comparison
def StripEllipSk(SketchValue: Sketch) -> Sketch:
    return ReplaceValue(
        SketchValue,
        entities=tuple(
            ReplaceValue(Value, provenance=None) for Value in SketchValue.entities
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )


# exact canonical readback coordinates carry ordinary geometric values rather than source archive bytes
def ReadEllipPoint(Value: object) -> tuple[float, float]:
    if type(Value) is not tuple or len(CastValue(tuple[object, ...], Value)) != 2:
        raise ValueError("SOLIDWORKS cold ellipse lacks a typed sketch station")
    First, Second = CastValue(tuple[object, object], Value)
    return RequireScalar(First), RequireScalar(Second)


# three source stations restore lost binary64 precision only when they project to the same public conic
def ReadColdEllip(DocumentValue: CadDocument) -> tuple[CadDocument, EllipsePlan]:
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "cold ellipse document name"
    )
    SyntheticValue = ColdReadInput(DocumentValue, NameValue, SketchReader=StripEllipSk)
    PlanValue = PlanEllipse(SyntheticValue)
    (SketchValue,) = DocumentValue.sketches
    RawValue = SketchValue.attributes.get(KEllipseStations)
    if type(RawValue) is not tuple or len(CastValue(tuple[object, ...], RawValue)) != 3:
        raise ValueError(
            "SOLIDWORKS cold ellipse lacks its three typed sketch stations"
        )
    Center, Major, Minor = map(ReadEllipPoint, CastValue(tuple[object, ...], RawValue))
    (Entity,) = SketchValue.entities
    if EllipAxisGeom(Center, Major, Minor, PlanValue.DepthValue) != Entity.geometry:
        raise ValueError(
            "SOLIDWORKS cold ellipse stations disagree with the public conic"
        )
    return SyntheticValue, ReplaceValue(
        PlanValue, CenterValue=Center, MajorValue=Major, MinorValue=Minor
    )
