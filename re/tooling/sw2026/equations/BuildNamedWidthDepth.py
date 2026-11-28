from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import (
    MakeBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.BindWidthMut import (
    BindWidthMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import (
    MakePartProfMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.SelectBlindEnd import (
    SelectBlindEnd,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import (
    MakeCornerMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import (
    MakeRectDimsMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

EPOCH = 1790000000


def break_owner(fault, boss, dimensions, system):
    active, dormant = boss.DimensionsValue[:2]
    if fault == "foreign_dormant_parameter":
        dormant.DimensionValue.FieldsValue["f28"] = dimensions[1].ParameterValue
    elif fault == "duplicate_dormant_identity":
        dormant.DimensionValue.FieldsValue["f50"] = active.DimensionValue.FieldsValue[
            "f50"
        ]
    elif fault == "active_reverse_slot":
        boss.EndValue.FieldsValue["f08"] = 0
    elif fault == "dormant_equation_clone":
        (equation,) = system.RootValue.FieldsValue["f9d0"].FieldsValue["f58"]["items"]
        (token,) = equation["o"].FieldsValue["f58"].FieldsValue["f10"]["items"]
        wrapper = token["o"].FieldsValue["f80"]
        handle = dormant.HandleValue
        wrapper.FieldsValue["f58"] = ArchiveNode(
            handle.ClassValue,
            {**handle.FieldsValue, "f58": MakeSelfComp(system.RootValue)},
        )
        wrapper.FieldsValue["f70"] = handle.FieldsValue["f4c"]
    elif fault not in (None, "height_dependency"):
        raise ValueError("unknown authored contrast")


def build_named(plan, dormant, fault=None):
    settings = MakePartRecipe(plan, EPOCH)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    margin = min(plan.WidthValue, plan.HeightValue) / 4
    label = RectDimInput(
        (plan.WidthValue / 2, -margin),
        (plan.WidthValue + margin, plan.HeightValue / 2),
        settings.DesignIntent,
        settings.SelectedLeader,
        False,
    )
    dims = MakeRectDimsMut(profile, label, allocator, plan.SketchDriverNames)
    MakeCornerMut(profile, system.OriginValue)
    end = replace(SelectBlindEnd(plan, None, None), DormantDepth=dormant)
    boss = MakeBlindMut(
        plan.FeatureName,
        system.RootValue,
        profile,
        end,
        settings.TargetValue,
        allocator,
        settings.DesignIntent,
        settings.SelectedLeader,
    )
    width = dims[1] if fault == "height_dependency" else dims[0]
    BindWidthMut(system.RootValue, width, boss.DimensionsValue[0])
    break_owner(fault, boss, dims, system)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    roots = (*system.FeatureValues, profile.ProfileValue, boss.FeatureValue)
    streams, _, _ = EmitPartStreams(
        system,
        roots,
        headers,
        definition,
        settings,
        plan,
        MakeSketchKeys(dims, settings.DocumentUnits.LengthUnit),
        PartRelations=True,
    )
    return BuildSldprt(streams, FormatVersion=4)
