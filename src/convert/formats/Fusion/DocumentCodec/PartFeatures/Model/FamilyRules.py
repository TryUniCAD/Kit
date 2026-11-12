from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRule import (
    FamilyRule,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

KFamilyRules: dict[type[object], FamilyRule] = {
    FilletSpec: FamilyRule("DcFilletEdgeFeature", "Fillet", 1, 8),
    ChamferSpec: FamilyRule("DcChamferFeature", "Chamfer", 1, 8),
    ShellSpec: FamilyRule("DcShellFeature", "Shell", 2, 16),
}


def FamilyOf(Feature: KPartFeature) -> FamilyRule:
    RuleValue = KFamilyRules.get(type(Feature))
    if RuleValue is None:
        raise ValueError("Unsupported Fusion part feature family")
    return RuleValue
