from math import isclose, isfinite

from ObliqueMassShape import document_values, shape


def require(value, message):
    if not value:
        raise ValueError(message)


def row(metadata, interface, name, kind=1):
    (value,) = [
        item
        for item in metadata["interfaces"][interface]["members"]
        if item["names"][0] == name and item["invoke_kind"] == kind
    ]
    return value


def binding(metadata):
    require(
        all(
            (value["major"], value["minor"]) == (34, 0)
            for value in metadata["libraries"].values()
        )
        and metadata["cad_objects_created"]
        == metadata["model_documents_opened"]
        == metadata["native_processes_started_by_tool"]
        == 0,
        "registered mass metadata scope differs",
    )
    value = row(metadata, "IModelDocExtension", "GetMassProperties2")
    require(
        value["member_id"] == 286
        and value["names"]
        == ["GetMassProperties2", "Accuracy", "Status", "UseSelected"]
        and value["arguments"] == [[3, 1, None], [[26, 3], 2, None], [11, 1, None]]
        and value["return_type"] == [12, 0, None],
        "registered mass output binding differs",
    )
    body = row(metadata, "IBody2", "GetMassProperties")
    require(
        body["member_id"] == 76
        and body["arguments"] == [[5, 1, None]]
        and body["return_type"] == [12, 0, None],
        "registered body-mass binding differs",
    )
    require(
        metadata["enums"]["swMassPropertiesStatus_e"]["swMassPropertiesStatus_OK"] == 0,
        "registered success status differs",
    )
    return {
        "member_id": 286,
        "invoke_kind": 1,
        "return_type": (12, 0),
        "argument_types": ((3, 1), (16387, 2), (11, 1)),
        "status_placeholder": -2147483648,
        "returned_shape": [
            "twelve documented metrics with an explicitly checked measured 2026 extension",
            "actual byref status",
        ],
        "accuracy_arguments": {"0": "as-is", "1": "default", "2": "maximum"},
        "mass_property2_accuracy_enum_used": False,
        "body_density_kg_m3": 1.0,
    }


def cast(author, value, metadata, interface):
    require(value is not None, "native mass interface is null")
    iid = author.sw.pythoncom.MakeIID(metadata["interfaces"][interface]["guid"])
    proxy = author.rec.call(
        "mass QueryInterface " + interface,
        value._oleobj_.QueryInterface,
        iid,
        author.sw.pythoncom.IID_IDispatch,
    )
    return author.sw.wc.Dispatch(proxy)


def metrics(value):
    require(
        isinstance(value, (tuple, list)) and len(value) == 12,
        "native mass result must contain twelve metrics",
    )
    require(
        all(type(item) in (int, float) and isfinite(item) for item in value),
        "native mass array contains nonfinite values",
    )
    values = [float(item) for item in value]
    require(
        values[3] > 0 and values[4] > 0, "native body has no positive volume and area"
    )
    return {
        "com": values[:3],
        "volume": values[3],
        "area": values[4],
        "mass": values[5],
        "inertia": values[6:],
        "raw_si": values,
    }


def comparisons(actual, expected):
    values = [
        ("volume", actual["volume"], expected["volume"]),
        ("area", actual["area"], expected["area"]),
    ]
    values.extend(
        ("com_" + str(index), first, second)
        for index, (first, second) in enumerate(
            zip(actual["com"], expected["com"], strict=True)
        )
    )
    return [
        {
            "name": name,
            "actual": first,
            "expected": second,
            "absolute_error": first - second,
            "relative_error": None if second == 0 else first / second - 1,
            "within_original_tolerance": isclose(
                first, second, rel_tol=2e-7, abs_tol=1e-12
            ),
        }
        for name, first, second in values
    ]


def collect(author, metadata, original_default, prediction=None):
    plan = binding(metadata)
    result = {
        "original_default": original_default,
        "binding": plan,
        "coordinate_domain": "unsited ordinary part default model coordinates, no assembly transform",
        "body_coordinate_domain": "API body creation coordinates; predicted to equal the ordinary unmoved part model frame and checked separately against its target",
        "units": {"length": "m", "area": "m^2", "volume": "m^3", "mass": "kg"},
        "use_selected": False,
        "levels": [],
        "body_measurements": [],
        "diagnostic_complete": False,
    }
    author.rec.data["mass_precision"] = result
    author.rec.flush()
    part = author.declared_interface(author.model, "IPartDoc")
    bodies = list(author.get(part, "GetBodies2", 0, False) or ())
    require(len(bodies) == 1, "mass diagnostic requires exactly one actual model body")
    result["actual_model_body_count"] = len(bodies)
    body = cast(author, bodies[0], metadata, "IBody2")
    extension = cast(
        author, author.get(author.model, "Extension"), metadata, "IModelDocExtension"
    )
    manager = author.get(author.model, "SelectionManager")
    result["selection_count_before"] = int(
        author.get(manager, "GetSelectedObjectCount2", -1)
    )
    author.get(author.model, "ClearSelection2", True)
    result["selection_count_for_explicit_calls"] = int(
        author.get(manager, "GetSelectedObjectCount2", -1)
    )
    require(
        result["selection_count_for_explicit_calls"] == 0,
        "mass diagnostic selection did not clear",
    )
    legacy = cast(
        author, author.get(extension, "CreateMassProperty"), metadata, "IMassProperty"
    )
    author.set(legacy, "UseSystemUnits", True)
    result["separate_legacy_context"] = {
        "use_system_units": bool(author.get(legacy, "UseSystemUnits")),
        "density": float(author.get(legacy, "Density")),
        "volume": float(author.get(legacy, "Volume")),
        "area": float(author.get(legacy, "SurfaceArea")),
        "com": [float(value) for value in author.get(legacy, "CenterOfMass")],
    }
    for label in ("before_explicit_accuracy", "after_explicit_accuracy"):
        if label == "after_explicit_accuracy":
            for level in (0, 1, 2):
                observed = {
                    "accuracy_argument": level,
                    "meaning": plan["accuracy_arguments"][str(level)],
                    "passed": False,
                }
                result["levels"].append(observed)
                try:
                    raw = author.rec.call(
                        "registered GetMassProperties2 accuracy " + str(level),
                        extension._oleobj_.InvokeTypes,
                        plan["member_id"],
                        0,
                        plan["invoke_kind"],
                        plan["return_type"],
                        plan["argument_types"],
                        level,
                        plan["status_placeholder"],
                        False,
                        parameters={
                            "accuracy": level,
                            "use_selected": False,
                            "out_status_is_returned_not_assumed": True,
                        },
                    )
                    observed["raw_shape"] = shape(raw)
                    author.rec.flush()
                    require(
                        isinstance(raw, tuple) and len(raw) == 2,
                        "mass call must return its variant and actual out status",
                    )
                    observed["status"] = raw[1]
                    require(
                        type(raw[1]) is int and raw[1] == 0,
                        "native mass status is not OK",
                    )
                    values, framing = document_values(raw, level)
                    observed.update(framing)
                    observed["metrics"] = metrics(values)
                    observed["versus_original_default"] = comparisons(
                        observed["metrics"], original_default
                    )
                    if prediction is not None:
                        observed["versus_unchanged_analytic"] = comparisons(
                            observed["metrics"], prediction
                        )
                    observed["passed"] = True
                except Exception as error:
                    observed["error"] = repr(error)
                author.rec.flush()
        observed = {
            "stage": label,
            "density_kg_m3": 1.0,
            "accuracy_parameter": None,
            "passed": False,
        }
        result["body_measurements"].append(observed)
        try:
            value = author.rec.call(
                "actual body mass " + label,
                body._oleobj_.InvokeTypes,
                76,
                0,
                1,
                (12, 0),
                ((5, 1),),
                1.0,
            )
            observed["raw_shape"] = shape(value)
            author.rec.flush()
            observed["metrics"] = metrics(value)
            observed["versus_original_default"] = comparisons(
                observed["metrics"], original_default
            )
            if prediction is not None:
                observed["versus_unchanged_analytic"] = comparisons(
                    observed["metrics"], prediction
                )
            observed["passed"] = True
        except Exception as error:
            observed["error"] = repr(error)
        author.rec.flush()
    result["default_after_explicit_accuracy"] = author.rec.call(
        "original default mass after explicit accuracy", author.sw.mass, author.model
    )
    result["diagnostic_complete"] = bool(
        result["separate_legacy_context"]["use_system_units"]
        and len(result["levels"]) == 3
        and all(value["passed"] for value in result["levels"])
        and len(result["body_measurements"]) == 2
        and all(value["passed"] for value in result["body_measurements"])
    )
    author.rec.flush()
    return result
