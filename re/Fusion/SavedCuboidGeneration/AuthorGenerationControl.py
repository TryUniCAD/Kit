from math import isclose

import adsk.core
import adsk.fusion


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def author_geometry(design, request):
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    component = design.rootComponent
    dimensions = request["dimensions_mm"]
    drivers, names = request["drivers"], request["names"]
    for role in ("width", "depth", "height"):
        value = adsk.core.ValueInput.createByString(f"{dimensions[role]} mm")
        require(design.userParameters.add(drivers[role], value, "mm", ""), f"Could not author {role} driver")

    point = adsk.core.Point3D.create
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = names["sketch"]
    width, depth = dimensions["width"] / 10, dimensions["depth"] / 10
    lines = sketch.sketchCurves.sketchLines
    bottom = lines.addByTwoPoints(point(0, 0, 0), point(width, 0, 0))
    right = lines.addByTwoPoints(bottom.endSketchPoint, point(width, depth, 0))
    top = lines.addByTwoPoints(right.endSketchPoint, point(0, depth, 0))
    left = lines.addByTwoPoints(top.endSketchPoint, bottom.startSketchPoint)
    bottom.startSketchPoint.isFixed = True
    rules = sketch.geometricConstraints
    for line, add in ((bottom, rules.addHorizontal), (right, rules.addVertical),
                      (top, rules.addHorizontal), (left, rules.addVertical)):
        require(add(line), "Could not author axis rule")
    orientations = adsk.fusion.DimensionOrientations
    for role, line, orientation, location in (
        ("width", bottom, orientations.HorizontalDimensionOrientation, point(width / 2, -0.5, 0)),
        ("depth", left, orientations.VerticalDimensionOrientation, point(-0.5, depth / 2, 0)),
    ):
        dimension = sketch.sketchDimensions.addDistanceDimension(
            line.startSketchPoint, line.endSketchPoint, orientation, location
        )
        require(dimension, f"Could not author {role} dimension")
        dimension.parameter.expression = drivers[role]
    require(sketch.isFullyConstrained and sketch.profiles.count == 1, "Independent rectangle did not constrain")

    extrusions = component.features.extrudeFeatures
    feature = extrusions.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    value = adsk.core.ValueInput.createByString(drivers["height"])
    extent = adsk.fusion.DistanceExtentDefinition.create(value)
    require(feature.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection), "Could not bind height")
    extrusion = extrusions.add(feature)
    require(extrusion, "Could not create independent extrusion")
    extrusion.name = names["extrude"]
    body = extrusion.bodies.item(0)
    body.name = names["body"]
    return body


def set_density(design, material, density):
    properties = {field.id: field for field in material.materialProperties}
    assigned = {}
    for property_id in ("structural_Density", "thermal_Density"):
        value_property = properties.get(property_id)
        field = adsk.core.FloatProperty.cast(value_property) if value_property else None
        if field is None and property_id == "thermal_Density":
            continue
        require(field is not None and not field.isReadOnly and not field.hasMultipleValues,
                f"Independent material has no writable scalar {property_id}")
        unit = field.units
        compact_unit = unit.casefold().replace(" ", "").replace("³", "3").replace("^", "")
        kilograms_per_cubic_metre = {"kg/m3", "kilogrampercubicmeter", "kilogrampercubicmetre", "kgm-3"}
        try:
            value = density if compact_unit in kilograms_per_cubic_metre else design.unitsManager.convert(density, "kg/m^3", unit)
        except RuntimeError as error:
            raise RuntimeError(f"Unsupported material density unit {unit!r} for {property_id}; original value {field.value!r}") from error
        require(value > 0, f"Unsupported material density unit {unit!r} for {property_id}")
        field.value = value
        assigned[property_id] = {"value": field.value, "unit": unit}
    return assigned


def assign_material(design, body, request, seed_material=None):
    values = request["material"]
    seed = seed_material if seed_material is not None else body.material
    require(seed, "No native material seed is available")
    copied = design.materials.addByCopy(seed, values["label"])
    require(copied, "Could not copy native material into the owned design")
    density_properties = set_density(design, copied, values["density_kg_m3"])
    body.material = copied
    require(body.material.id == copied.id and body.material.name == values["label"],
            "Independent physical material assignment failed")

    current = copied.appearance
    use_material_appearance = (
        current is not None and current.parent == design
        and any(field.id == "opaque_albedo" for field in current.appearanceProperties)
    )
    appearance = current if use_material_appearance else design.appearances.add(values["label"] + " color")
    require(appearance, "Could not create a document-owned opaque appearance")
    channels = [round(channel * 255) for channel in values["rgba"]]
    require(all(abs(value * 255 - channel) <= 1e-4 for value, channel in zip(values["rgba"], channels, strict=True))
            and channels[3] == 255, "Oracle color must use exact opaque eight-bit channels")
    appearance.color = adsk.core.Color.create(*channels)
    if not use_material_appearance:
        body.appearance = appearance
    require(body.appearance.id == appearance.id, "Independent appearance assignment failed")
    color = body.appearance.color
    require([color.red, color.green, color.blue, color.opacity] == channels, "Independent appearance color differs")
    return {
        "seed_material_id": seed.id,
        "seed_material_name": seed.name,
        "material_id": copied.id,
        "appearance_id": appearance.id,
        "appearance_uses_material": use_material_appearance,
        "appearance_source_type": int(body.appearanceSourceType),
        "density_properties": density_properties,
        "rgba8": channels,
    }


def author_control(document, request, seed_material=None):
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    require(design is not None, "Independent document lacks a Fusion design")
    root = design.rootComponent
    require(not document.isSaved and not root.sketches.count
            and not root.bRepBodies.count and not root.occurrences.count,
            "Independent control requires a fresh blank scene")
    document.name = request["title"]
    body = author_geometry(design, request)
    report = assign_material(design, body, request, seed_material)
    require(design.computeAll(), "Independent control could not rebuild")
    physical = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
    expected_density = request["material"]["density_kg_m3"] / 1_000_000
    require(isclose(physical.density, expected_density, rel_tol=1e-8, abs_tol=0),
            "Independent control could not apply the requested physical density")
    require(isclose(physical.mass, expected_density * body.volume, rel_tol=1e-8, abs_tol=0),
            "Independent control physical mass does not match density and volume")
    report["body_density_kg_cm3"] = physical.density
    report["body_mass_kg"] = physical.mass
    report["document_name"] = document.name
    report["root_component_name"] = root.name
    return design, report
