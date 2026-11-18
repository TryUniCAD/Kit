from __future__ import annotations

from math import isclose, isfinite
from pathlib import Path

from AuthorCurves import require
from PerpendicularSourcePlan import AXES, PARAMETERS, dot, expected_transforms, geometry, normal, orthogonality


def same_file(value, expected):
    actual = Path(str(value))
    return actual.is_file() and actual.samefile(expected)


def configuration(author, model, expected):
    actual = str(author.get(author.get(model, "GetActiveConfiguration"), "Name"))
    require(list(author.get(model, "GetConfigurationNames") or ()) == [expected] and actual == expected,
            "the source requires exactly its authored active configuration")
    return actual


def component_map(author, assembly, case, expected_child):
    result = {}
    values = author.get(assembly, "GetComponents", True) or ()
    require(len(values) == 2 and int(author.get(assembly, "GetComponentCount", False)) == 2, "the source has an unexpected component hierarchy")
    for value in values:
        component = author.typed(value, "Component2")
        name = str(author.get(component, "Name2"))
        require(name in [case["child_name"] + "-1", case["child_name"] + "-2"] and name not in result,
                "the resolved native occurrence identity differs")
        require(same_file(author.get(component, "GetPathName"), expected_child), "the component resolves outside its exact owned child")
        result[name] = component
    return [result[case["child_name"] + "-" + str(index)] for index in (1, 2)]


def author_mate(author, model, assembly, components, case):
    import Swapp

    for component in components:
        if author.get(component, "IsFixed"):
            author.get(model, "ClearSelection2", True)
            require(bool(author.get(component, "Select4", False, Swapp.nothing(), False)), "the initial component could not be selected")
            author.get(assembly, "UnfixComponent")
            require(not author.get(component, "IsFixed"), "the initial native component could not be floated")
    anchor = components[case["fixed_occurrence"]]
    author.get(model, "ClearSelection2", True)
    require(bool(author.get(anchor, "Select4", False, Swapp.nothing(), False)), "the fixed anchor could not be selected")
    author.get(assembly, "FixComponent")
    require(bool(author.get(anchor, "IsFixed")), "the selected anchor did not become fixed")
    author.get(model, "ClearSelection2", True)
    extension = author.get(model, "Extension")
    title = Path(str(author.get(model, "GetTitle"))).stem
    for ordinal, (index, plane) in enumerate(case["mate"]["planes"]):
        selection = f"{plane}@{author.get(components[index], 'Name2')}@{title}"
        require(bool(author.get(extension, "SelectByID2", selection, "PLANE", 0.0, 0.0, 0.0, ordinal > 0, 1, Swapp.nothing(), 0)),
                "the ordinary perpendicular endpoint selection failed")
    error = Swapp.byref_long()
    result = author.get(assembly, "AddMate5", 2, case["mate"]["api_alignment"], False, 0.0, 0.0, 0.0,
                        1.0, 1.0, 0.0, 0.0, 0.0, False, False, 0, error)
    require(result is not None and int(error.value) == 1, "the perpendicular source was rejected by the native mate API")
    author.get(model, "ClearSelection2", True)


def reference_identity(author, entity, feature):
    import Swapp

    reference = author.get(entity, "Reference")
    again = author.get(entity, "Reference")
    specific = author.get(feature, "GetSpecificFeature2")
    repeated = author.get(feature, "GetSpecificFeature2")
    require(reference is not None and again is not None and specific is not None and repeated is not None,
            "the datum reference cannot be resolved to a native object")
    return {"repeated_reference": int(Swapp.invoke(author.app, "IsSame", reference, again)),
            "repeated_specific": int(Swapp.invoke(author.app, "IsSame", specific, repeated)),
            "expected_feature": int(Swapp.invoke(author.app, "IsSame", reference, feature)),
            "expected_specific": int(Swapp.invoke(author.app, "IsSame", reference, specific)),
            "specific_equality_is_diagnostic": True}


def mate_state(author, model, child, components, rows, case):
    from AssemblyMateEvidence import mate_features, require_plane

    features = list(mate_features(author, model))
    require(len(features) == 1, "the source does not own exactly one ordinary mate")
    feature = features[0]
    mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
    name = str(author.get(feature, "Name"))
    require(name == case["mate"]["name"] and author.get(feature, "GetTypeName2") == "MatePerpendicular"
            and not author.get(feature, "IsSuppressed") and int(author.get(mate, "Type")) == 2
            and int(author.get(mate, "GetMateEntityCount")) == 2, "the native perpendicular feature identity differs")
    require(author.get(feature, "GetFirstDisplayDimension") is None, "the ordinary perpendicular mate unexpectedly owns a driving scalar display")
    endpoints = []
    for ordinal, (index, plane) in enumerate(case["mate"]["planes"]):
        entity = author.typed(author.get(mate, "MateEntity", ordinal), "MateEntity2")
        component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
        selected = author.get(component, "FeatureByName", plane)
        original = author.get(child, "FeatureByName", plane)
        values = [float(value) for value in author.get(entity, "EntityParams") or ()]
        require(len(values) == 8 and all(map(isfinite, values)) and int(author.get(entity, "ReferenceType2")) == 4,
                "the mate endpoint is not an ordinary finite datum plane")
        require(str(author.get(component, "Name2")) == rows[index]["name"] and int(author.get(component, "GetID")) == rows[index]["native_id"],
                "the ordered mate endpoint lost its exact occurrence")
        require(selected is not None and original is not None and author.get(selected, "GetTypeName2") == "RefPlane"
                and int(author.get(selected, "GetID")) == int(author.get(original, "GetID")), "the component datum does not belong to its actual loaded child")
        row = {"occurrence": rows[index]["name"], "occurrence_native_id": rows[index]["native_id"],
               "plane": plane, "plane_native_id": int(author.get(original, "GetID")), "reference_type": 4,
               "point": values[:3], "normal": values[3:6], "object_comparison": reference_identity(author, entity, selected)}
        require_plane(row, rows[index]["transform"], plane)
        endpoints.append(row)
    residual = dot(endpoints[0]["normal"], endpoints[1]["normal"])
    require(abs(residual) <= 1e-10, "the measured mate endpoints are not orthogonal")
    return {"name": name, "type": 2, "native_feature_id": int(author.get(feature, "GetID")),
            "alignment_observed": int(author.get(mate, "Alignment")), "ordered_endpoints": endpoints, "normal_dot": residual}


def capture(author, model, assembly, child_path, case, edited=False):
    import Swapp
    from AuthorAssemblySources import feature_tree, transform_matches

    matrices = expected_transforms(case, edited)
    objects = component_map(author, assembly, case, child_path)
    rows, identifiers = [], set()
    child = author.get(objects[0], "GetModelDoc2")
    require(child is not None and same_file(author.get(child, "GetPathName"), child_path), "the actual child model is unavailable")
    configuration(author, model, case["configuration"])
    configuration(author, child, case["configuration"])
    for index, component in enumerate(objects):
        values = [float(value) for value in author.get(author.typed(author.get(component, "Transform2"), "MathTransform"), "ArrayData")]
        identifier = int(author.get(component, "GetID"))
        require(identifier not in identifiers and transform_matches(values, matrices[index]), "the native pose or occurrence ID differs from the independent design")
        identifiers.add(identifier)
        resolved = author.get(component, "GetModelDoc2")
        require(resolved is not None and same_file(author.get(resolved, "GetPathName"), child_path)
                and str(author.get(component, "ReferencedConfiguration")) == case["configuration"]
                and not author.get(component, "IsSuppressed") and not author.get(component, "IsHidden", False)
                and bool(author.get(component, "IsFixed")) == (index == case["fixed_occurrence"]), "the native component state changed")
        require(len(author.get(author.typed(resolved, "PartDoc"), "GetBodies2", 0, True) or ()) == 1,
                "the ordinary source requires one solid per child")
        rows.append({"name": str(author.get(component, "Name2")), "native_id": identifier, "transform": values,
                     "fixed": index == case["fixed_occurrence"], "configuration": case["configuration"], "visible_child_bodies": 1})
    expected = geometry(case, edited)
    metrics = {}
    for role, target in (("child", child), ("assembly", model)):
        require(int(author.get(author.get(target, "Extension"), "GetWhatsWrongCount")) == 0, "the native source has errors or warnings")
        metrics[role] = author.rec.call("measure independent " + role + " geometry", Swapp.mass, target)
        actual = metrics[role]
        require(isinstance(actual, dict) and "error" not in actual and actual.get("mass", 0) > 0, "native mass properties are unavailable")
        for key in ("volume", "area"):
            author.rec.close_number(role + " " + key, actual[key], expected[role][key], absolute=1e-15)
        for axis, (actual_value, wanted) in enumerate(zip(actual["com"], expected[role]["com"], strict=True)):
            author.rec.close_number(role + " centroid " + str(axis), actual_value, wanted, absolute=1e-12)
    dimensions = {}
    size = [*case["child_size_m"][:2], case["edit_depth_m"] if edited else case["child_size_m"][2]]
    for name, wanted in zip(PARAMETERS, size, strict=True):
        parameter = author.get(child, "Parameter", name)
        require(parameter is not None and author.get(parameter, "DrivenState") == 2 and not author.get(parameter, "ReadOnly"),
                "the native source lost an editable authored child parameter")
        dimensions[name] = float(author.get(parameter, "SystemValue"))
        author.rec.close_number(name, dimensions[name], wanted)
    require(abs(orthogonality(case, [row["transform"] for row in rows])) <= 1e-10, "the measured placements do not satisfy perpendicularity")
    return {"occurrences": rows, "body_count": 2, "mass": metrics, "dimensions_m": dimensions,
            "tree": feature_tree(author, model), "child_tree": feature_tree(author, child),
            "mate": mate_state(author, model, child, objects, rows, case)}


def signature(value):
    return {"tree": value["tree"], "child_tree": value["child_tree"], "body_count": value["body_count"],
            "occurrences": [{key: row[key] for key in ("name", "native_id", "configuration", "fixed", "visible_child_bodies")}
                            for row in value["occurrences"]],
            "mate": {key: value["mate"][key] for key in ("name", "type", "native_feature_id", "alignment_observed")}
            | {"ordered_endpoints": [{key: endpoint[key] for key in ("occurrence", "occurrence_native_id", "plane", "plane_native_id", "reference_type")}
                                     for endpoint in value["mate"]["ordered_endpoints"]]}}


def edit_live(author, model, assembly, child, child_path, case):
    import Swapp

    objects = component_map(author, assembly, case, child_path)
    desired = expected_transforms(case, True)[1 - case["fixed_occurrence"]]
    utility = author.get(author.app, "GetMathUtility")
    transform = author.get(utility, "CreateTransform", Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, desired))
    require(transform is not None and bool(author.get(objects[1 - case["fixed_occurrence"]], "SetTransformAndSolve2", transform)),
            "the live valid reorientation was rejected")
    dimension = author.get(child, "Parameter", PARAMETERS[2])
    require(dimension is not None and int(author.get(dimension, "SetSystemValue3", case["edit_depth_m"], 1, Swapp.nothing())) == 0,
            "the live child depth edit was rejected")
    require(bool(author.get(child, "ForceRebuild3", False)) and bool(author.get(model, "ForceRebuild3", False)),
            "the live source rebuild failed")
