# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import adsk.core


def observe_camera(viewport):
    camera = viewport.camera
    observation = {
        "eye_cm": camera.eye.asArray(),
        "target_cm": camera.target.asArray(),
        "up": camera.upVector.asArray(),
        "projection": int(camera.cameraType),
        "visual_style": int(viewport.visualStyle),
        "viewport_pixels": [viewport.width, viewport.height],
    }
    projection_types = adsk.core.CameraTypes
    if camera.cameraType == projection_types.OrthographicCameraType:
        success, width, height = camera.getExtents()
        if not success:
            raise RuntimeError("Fusion could not measure orthographic camera extents")
        observation["extents_cm"] = [width, height]
    elif camera.cameraType in (projection_types.PerspectiveCameraType, projection_types.PerspectiveWithOrthoFacesCameraType):
        observation["perspective_angle_rad"] = camera.perspectiveAngle
    else:
        raise ValueError(f"Unsupported Fusion camera projection {observation['projection']}")
    return observation


def property_value(value):
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, (list, tuple)):
        return [property_value(element) for element in value]
    if isinstance(value, adsk.core.Color):
        return [value.red, value.green, value.blue, value.opacity]
    raise TypeError("Unsupported native property value")


def observe_properties(properties):
    observations = []
    for item in properties:
        row = {"id": item.id, "type": item.objectType}
        if hasattr(item, "units"):
            row["unit"] = item.units
        if hasattr(item, "hasConnectedTexture"):
            row["has_connected_texture"] = item.hasConnectedTexture
        if row.get("has_connected_texture"):
            row["unavailable"] = "connected texture value"
        else:
            try:
                if getattr(item, "hasMultipleValues", False):
                    row["values"] = property_value(item.values)
                else:
                    row["value"] = property_value(item.value)
            except (AttributeError, TypeError):
                row["unavailable"] = "native property value"
        observations.append(row)
    return sorted(observations, key=lambda row: row["id"])


def observe_visibility(entity):
    return {
        "name": entity.name,
        "visible": entity.isVisible,
        "lightbulb_on": entity.isLightBulbOn,
    }


def observe_loaded_presentation(viewport, design):
    camera = observe_camera(viewport)
    appearances = {}

    def remember_appearance(appearance):
        if appearance is None:
            return None
        identity = appearance.id
        if identity not in appearances:
            appearances[identity] = {
                "id": identity,
                "name": appearance.name,
                "properties": observe_properties(appearance.appearanceProperties),
            }
        return identity

    def observe_material(material):
        return {
            "id": material.id,
            "name": material.name,
            "appearance_id": remember_appearance(material.appearance),
            "properties": observe_properties(material.materialProperties),
        }

    def observe_assignment(entity):
        return {
            "appearance_id": remember_appearance(entity.appearance),
            "source_type": int(entity.appearanceSourceType),
        }

    root = design.rootComponent
    if root.occurrences.count or root.bRepBodies.count != 1 or root.sketches.count != 1:
        raise ValueError("Presentation observation requires a single root body and sketch")
    body = root.bRepBodies.item(0)
    if body.faces.count != 6 or not body.isSolid:
        raise ValueError("Presentation observation requires a solid six-face body")
    if body.material is None:
        raise ValueError("Cuboid has no effective physical material")

    for appearance in design.appearances:
        remember_appearance(appearance)
    materials = {material.id: observe_material(material) for material in design.materials}
    if body.material.id not in materials:
        materials[body.material.id] = observe_material(body.material)

    faces = []
    for face in body.faces:
        sample = face.pointOnFace
        success, normal = face.evaluator.getNormalAtPoint(sample)
        if not success:
            raise RuntimeError("Fusion could not measure cuboid face normal")
        faces.append({
            "outward_normal": normal.asArray(),
            "point_cm": sample.asArray(),
            "appearance": observe_assignment(face),
        })

    body_appearance = observe_assignment(body)
    return {
        "camera": camera,
        "sketch_visibility": observe_visibility(root.sketches.item(0)),
        "body_visibility": observe_visibility(body),
        "body_material_id": body.material.id,
        "body_appearance": body_appearance,
        "faces": faces,
        "materials": [materials[identity] for identity in sorted(materials)],
        "appearances": [appearances[identity] for identity in sorted(appearances)],
    }
