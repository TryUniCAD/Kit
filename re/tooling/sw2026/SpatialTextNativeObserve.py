from __future__ import annotations

from math import isfinite

from AuthorCurves import require
from OriginNativeObserve import child_state as base_child_state, observe as base_observe


def annotation_positions(author, child, case):
    saved = author.model, author.sketch
    try:
        author.model = child
        feature = author.get(child, "FeatureByName", case["sketch_name"])
        require(feature is not None, "spatial text actual sketch feature is absent")
        author.sketch = author.get(feature, "GetSpecificFeature2")
        manager = author.get(author.sketch, "RelationManager")
        result = []
        for relation in author.get(manager, "GetRelations", 0) or ():
            if int(author.get(relation, "GetRelationType")) != 1:
                continue
            display = author.get(relation, "GetDisplayDimension")
            require(display is not None, "spatial text driving relation has no actual display dimension")
            dimension = author.get(display, "GetDimension2", 0)
            require(dimension is not None, "spatial text actual display has no value dimension")
            full_name = str(author.get(dimension, "FullName"))
            short_name = "@".join(full_name.split("@")[:2])
            require(short_name in case["parameter_names"][:2], "spatial text relation targets another actual parameter")
            annotation = author.get(display, "GetAnnotation")
            require(annotation is not None, "spatial text actual display has no annotation object")
            annotation = author.typed(annotation, "Annotation")
            position = author.get(annotation, "GetPosition")
            require(isinstance(position, (list, tuple)) and len(position) == 3
                    and all(type(value) in (float, int) and isfinite(value) for value in position),
                    "spatial text annotation returned no complete finite three-coordinate API position")
            result.append({"dimension_full_name": full_name, "parameter_name": short_name,
                           "parameter_value_m": float(author.get(dimension, "SystemValue")),
                           "annotation_get_position_m": [float(value) for value in position],
                           "coordinate_owner": "actual relation display -> IDisplayDimension.GetAnnotation -> IAnnotation.GetPosition",
                           "stored_moDimText_point_equality_asserted": False})
        require(len(result) == 2 and {row["parameter_name"] for row in result} == set(case["parameter_names"][:2]),
                "spatial text annotation capture lacks exactly both actual driving displays")
        return sorted(result, key=lambda row: case["parameter_names"].index(row["parameter_name"]))
    finally:
        author.model, author.sketch = saved


def child_state(author, child, case, edited, initial=False):
    result = base_child_state(author, child, case, edited, initial)
    result["annotation_coordinates"] = annotation_positions(author, child, case)
    return result


def observe(author, model, case, native_path, edited, moved, initial=False):
    result = base_observe(author, model, case, native_path, edited, moved, initial)
    drawing = author.typed(model, "DrawingDoc")
    sheet = author.typed(author.get(drawing, "GetFirstView"), "View")
    view = author.typed(author.get(sheet, "GetNextView"), "View")
    child = author.get(view, "ReferencedDocument")
    require(child is not None, "spatial text drawing has no actual resolved child")
    result["child"]["annotation_coordinates"] = annotation_positions(author, child, case)
    return result
