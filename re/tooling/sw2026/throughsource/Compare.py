from math import isclose

from Coverage import native_role
from Predict import predict
from Shape import frame, read_shape


def differences(left, right, path="", result=None):
    result = [] if result is None else result
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        if len(left) != len(right):
            result.append(
                {"path": path, "source_count": len(left), "candidate_count": len(right)}
            )
        for index, (source, candidate) in enumerate(zip(left, right)):
            differences(source, candidate, path + "/" + str(index), result)
    elif isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                result.append(
                    {
                        "path": path + "/" + key,
                        "missing_from": "source" if key not in left else "candidate",
                    }
                )
            else:
                differences(left[key], right[key], path + "/" + key, result)
    elif (
        isinstance(left, (float, int))
        and not isinstance(left, bool)
        and isinstance(right, (float, int))
        and not isinstance(right, bool)
    ):
        if not isclose(left, right, rel_tol=1e-10, abs_tol=1e-12):
            result.append({"path": path, "source": left, "candidate": right})
    elif left != right:
        result.append({"path": path, "source": left, "candidate": right})
    return result


def structural(document):
    ids = {}
    for domain in (
        document.feature_timeline,
        document.sketches,
        document.support_planes,
        document.configurations,
    ):
        for value in domain:
            ids[value.id] = value.name
    for value in document.parameters:
        ids[value.id] = ids.get(value.owner_id, value.owner_id) + ":" + value.name
    rows = []
    for value in document.feature_timeline:
        row = native_role(value)
        row.pop("source_id")
        row["input_feature_ids"] = tuple(
            ids.get(item, item) for item in value.input_feature_ids
        )
        row["sketch_id"] = ids.get(value.sketch_id, value.sketch_id)
        row["parameter_ids"] = tuple(
            ids.get(item, item) for item in value.parameter_ids
        )
        row["selection_ids"] = tuple(
            next(
                (
                    selection.name
                    for selection in document.selections
                    if selection.id == item
                ),
                item,
            )
            for item in value.selection_ids
        )
        rows.append(row)
    return {
        "history": rows,
        "configuration": tuple(
            {
                "name": value.name,
                "active": value.active,
                "parent": ids.get(value.parent_id, value.parent_id),
                "suppressed": tuple(
                    ids.get(item, item) for item in value.suppressed_feature_ids
                ),
                "overrides": tuple(str(item) for item in value.overrides),
                "custom_properties": dict(
                    value.attributes.get("custom_properties", {})
                ),
            }
            for value in document.configurations
        ),
        "body": tuple(
            {
                "name": value.name,
                "final_feature": ids.get(
                    value.final_feature_id, value.final_feature_id
                ),
                "material_id": value.material_id,
            }
            for value in document.bodies
        ),
        "planes": tuple(
            {
                "name": value.name,
                "transform": frame(value),
                "support_selection": value.support_selection_id,
                "offset_parameter": ids.get(
                    value.offset_parameter_id, value.offset_parameter_id
                ),
            }
            for value in document.support_planes
        ),
        "text": {
            "summary": dict(document.metadata.get("document_summary", {})),
            "file": dict(document.metadata.get("custom_properties", {})),
        },
    }


def shape_signature(shape):
    return {
        "support_axis": shape["support_axis"],
        "support": shape["support"],
        "rectangle": {key: shape["stock"][key] for key in ("minimum", "maximum")},
        "circle": {key: shape["tool"][key] for key in ("center", "radius")},
        "depth": shape["depth"],
        "cut_reversed": shape["cut_reversed"],
        "second_through_all": shape["second_through_all"],
        "configuration_name": shape["configuration_name"],
        "scope_mode": shape["scope"]["mode"],
    }


def compare(source, candidate):
    original, generated = read_shape(source), read_shape(candidate)
    shape_diff = differences(
        shape_signature(original), shape_signature(generated), "shape"
    )
    history_diff = differences(structural(source), structural(candidate), "portable")
    prediction_diff = differences(predict(original), predict(generated), "prediction")
    return {
        "shape_equal": not shape_diff,
        "ordered_portable_history_equal": not history_diff,
        "independent_prediction_equal": not prediction_diff,
        "differences": shape_diff + history_diff + prediction_diff,
        "full_original_equivalence": False,
        "qualification": "blocked until actual system/presentation/provenance owners and controlled native paired lifecycle qualify",
        "native_acceptance": False,
    }
