from dataclasses import replace

from SpatialTextMut import actual_displays, place_text_mut, point3, require

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite


def placements(child, labels):
    sketch, = child.sketches
    require(type(labels) is list and len(labels) == 2,
            "rectangle label intent requires exactly two complete driving labels")
    by_parameter = {}
    for row in labels:
        require(type(row) is dict and set(row) == {"sketch_id", "parameter_id", "text_point_m", "route_centerline"},
                "rectangle label intent has unknown or missing fields")
        require(type(row["parameter_id"]) is str and row["parameter_id"] in sketch.parameter_ids
                and row["sketch_id"] == sketch.id and row["parameter_id"] not in by_parameter,
                "rectangle label must select its actual unique driving parameter and sketch")
        require(type(row["route_centerline"]) is bool,
                "rectangle label centreline routing requires an explicit boolean")
        by_parameter[row["parameter_id"]] = (point3(row["text_point_m"]), row["route_centerline"])
    return tuple(by_parameter[identity] for identity in sketch.parameter_ids)


def make_group(document, native_parent, event, labels):
    plan = PlanAsmWrite(document, native_parent, event)
    child = plan.ChildDocument
    recipe = plan.ChildRecipe
    prism = ProjectRectDims(child)
    require(prism.AxisValue == "z" and not prism.Reversed and len(child.support_planes) == 1,
            "rectangle label intent requires the canonical Front-plane blind profile")
    CheckPartInput(child, recipe, prism)
    intent = placements(child, labels)
    ((width, _), (height, _)) = intent
    planar = replace(plan.ChildDimensions, WidthText=width[:2], HeightText=height[:2], RouteCenter=False)
    allocated = PersistentIds()
    system = MakePartBaseMut(recipe, prism, allocated)
    profile = MakePartProfMut(system, recipe, prism, allocated)
    drivers = MakeRectDimsMut(profile, planar, allocated, prism.SketchDriverNames)
    for (display, value, parameter), driver, (xyz, routed) in zip(
        actual_displays(profile.ProfileValue), drivers, intent, strict=True
    ):
        require(display is driver.DisplayValue and value is driver.DimensionValue and parameter is driver.ParameterValue
                and driver.HandleValue is display.FieldsValue["f850"][0]["o"]
                and display.FieldsValue["f1014"] == 0,
                "fresh rectangle publication must retain the actual value, parameter and display handle")
        text = display.FieldsValue["f6a0"]["f38"]
        require((text["x"], text["y"]) == xyz[:2] and text["z"] == 0.0,
                "rectangle witnesses must derive from the authored XY before whole-point placement")
        place_text_mut(display, xyz)
        display.FieldsValue["f1014"] = 0x800 if routed else 0
    keys = MakeSketchKeys(drivers, recipe.DocumentUnits.LengthUnit)
    part = FinishBlindMut(system, profile, recipe, prism, allocated, keys)
    bundle = MakePlanarGroup(part, plan.RootRecipe, plan.Occurrences, plan.MatesValue, plan.FixedIndex)
    require(bundle.ChildValue is part, "assembly linkage must use the actual generated dimensioned part")
    return bundle
