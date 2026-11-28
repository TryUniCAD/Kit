from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureContract import FeatureDef
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.TypeRegistry import RegisterTypes

from MakeLocalPatternDrivers import PatternDriverStyle


@dataclass(frozen=True, slots=True)
class PlaneIntersectionAxis(FeatureDef):
    first_plane_selection_id: str
    second_plane_selection_id: str
    start_mm: SpaceVector
    end_mm: SpaceVector


@dataclass(frozen=True, slots=True)
class AnnotationViewIntent:
    name: str
    basis: tuple[tuple[float, float, float], ...]


@dataclass(frozen=True, slots=True)
class AngularLabelIntent:
    parameter_id: str
    annotation_view: str
    design_intent: bool
    selected_leader: int
    shifted_point_m: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class PatternPresentation:
    angle: AngularLabelIntent
    count_parameter_id: str
    pitch_parameter_id: str
    styles: tuple[PatternDriverStyle, ...]
    views: tuple[AnnotationViewIntent, ...]
    active: str | None
    shown: tuple[str | None, ...]


@dataclass(frozen=True, slots=True)
class NeutralPatternInput:
    document: CadDocument
    output: SelfFileInput
    presentation: PatternPresentation


def register_input_types(*, with_axis=True):
    RegisterTypes(NeutralPatternInput, SelfFileInput, PatternPresentation, AngularLabelIntent,
                  PatternDriverStyle, AnnotationViewIntent)
    if with_axis:
        RegisterTypes(PlaneIntersectionAxis)
