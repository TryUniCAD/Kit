from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureKinds import CombineFeature
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve

KCreatorTypes = (DistanceExtrude, PlaneExtrude, AngularRevolve, PlaneRevolve)
KDefinitionKinds: dict[type[object], FeatureKind] = {
    DistanceExtrude: FeatureKind.KExtrusion,
    PlaneExtrude: FeatureKind.KExtrusion,
    AngularRevolve: FeatureKind.KRevolution,
    PlaneRevolve: FeatureKind.KRevolution,
    BoundDatum: FeatureKind.KReference,
    BoundScale: FeatureKind.KScale,
    CombineFeature: FeatureKind.KBoolean,
}
