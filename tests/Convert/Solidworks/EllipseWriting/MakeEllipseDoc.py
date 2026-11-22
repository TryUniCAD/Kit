from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from json import loads as LoadJson
from typing import cast as CastValue

from interchange.Enums.EnumGeometry import GeometryKind
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc

# exact authored semiaxes and unit directions stay independent of host trigonometric rounding
KEllipseCases = (
    (
        "EllipseFrontA",
        (18.25, -6.375),
        (0.8767267557075077, 0.48098876891938763),
        (21.375, 8.875),
        13.125,
    ),
    (
        "EllipseFrontB",
        (-12.375, 9.125),
        (0.7518398074789775, -0.6593458151000688),
        (17.625, 11.25),
        21.625,
    ),
)

# hosted integration consumes disclosed measurements and independent clear stream evidence
KEvidenceRoot = (
    FilePath(__file__).resolve().parents[4] / "re/solidworks/measurements/2026"
)


# the test reuses the neutral part scaffold while supplying its own editable conic and labels
def MakeEllipseDoc(SlotValue: int) -> CadDocument:
    NameValue, Center, Direction, Radii, Depth = KEllipseCases[SlotValue]
    BaseValue = MakePlainDoc(NameValue, ((0.0, 0.0), (2.0, 0.0), (0.0, 2.0)), Depth)
    Entity = SketchEntity(
        "entity/full-ellipse",
        GeometryKind.KEllipse,
        EllipseGeometry(PlaneVector(*Center), PlaneVector(*Direction), *Radii),
    )
    Sketch = ReplaceValue(
        BaseValue.sketches[0],
        name="EllipseProfile",
        entities=(Entity,),
        closed_profile_entity_ids=((Entity.id,),),
    )
    return ReplaceValue(
        BaseValue,
        configurations=(ReplaceValue(BaseValue.configurations[0], name="Default"),),
        sketches=(Sketch,),
        feature_timeline=(
            ReplaceValue(BaseValue.feature_timeline[0], name="EllipseBoss"),
        ),
        bodies=(ReplaceValue(BaseValue.bodies[0], name="EllipseBoss"),),
    )


# receipt rows bind the runtime publication input to its independently recorded source digest
def ReadEllipseCase(
    SlotValue: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, str]]:
    Receipt = CastValue(
        dict[str, object],
        LoadJson((KEvidenceRoot / "SdkColdEllipseReceipt01.json").read_bytes()),
    )
    CaseValue = CastValue(list[dict[str, object]], Receipt["cases"])[SlotValue]
    Proof = CastValue(
        dict[str, object],
        LoadJson((KEvidenceRoot / "SdkScopedEllipse01.json").read_bytes()),
    )
    ProofRow = CastValue(list[dict[str, object]], Proof["results"])[SlotValue]
    return (
        Receipt,
        CaseValue,
        CastValue(dict[str, str], ProofRow["clear_stream_hashes"]),
    )
