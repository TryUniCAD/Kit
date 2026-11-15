from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureKinds import (
    CombineFeature,
    FilletFeature,
    ScaleFeature,
    ShellFeature,
)
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import ParameterValue

KAmount = ParameterValue(1.0, ValueKind.KLength, "mm")
KModifierSpecs: dict[str, tuple[FeatureKind, FeatureDef, tuple[str, ...]]] = {
    "CombineEmpty": (FeatureKind.KBoolean, CombineFeature(), ()),
    "CombineOne": (FeatureKind.KBoolean, CombineFeature(), ("extrude",)),
    "CombineRepeated": (FeatureKind.KBoolean, CombineFeature(), ("extrude", "extrude")),
    "CombineReference": (FeatureKind.KBoolean, CombineFeature(), ("sketch", "extrude")),
    "CombineInactive": (FeatureKind.KBoolean, CombineFeature(), ("extrude", "other")),
    "CombineBadOperation": (
        FeatureKind.KBoolean,
        CombineFeature(BooleanOp.KCreate),
        ("extrude", "other"),
    ),
    "CombineValid": (FeatureKind.KBoolean, CombineFeature(), ("extrude", "other")),
    "FilletEmpty": (FeatureKind.KFillet, FilletFeature(KAmount), ()),
    "ShellReference": (FeatureKind.KShell, ShellFeature(KAmount), ("sketch",)),
    "ScaleEmpty": (FeatureKind.KScale, ScaleFeature(SpaceVector(1.0, 1.0, 1.0)), ()),
    "MismatchedKind": (FeatureKind.KScale, CombineFeature(), ("extrude",)),
}
KModifierCases = tuple(
    NameValue for NameValue in KModifierSpecs if NameValue != "CombineValid"
)
