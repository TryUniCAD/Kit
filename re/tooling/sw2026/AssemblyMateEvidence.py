from __future__ import annotations

import math
from pathlib import Path

import Swapp
from AuthorCurves import require


TYPES = {"coincident": 0, "parallel": 3, "distance": 5}
PLANE_AXES = {"Right Plane": 0, "Top Plane": 1, "Front Plane": 2}


def author_plane_mates(author, model, assembly, components, case):
    extension = author.get(model, "Extension")
    title = Path(str(author.get(model, "GetTitle"))).stem
    names = [str(author.get(component, "Name2")) for component in components]
    anchor = case["fixed_occurrence"]
    author.get(model, "ClearSelection2", True)
    require(bool(author.get(components[anchor], "Select4", False, Swapp.nothing(), False)),
            "the native mate anchor could not be selected")
    author.get(assembly, "FixComponent")
    require(bool(author.get(components[anchor], "IsFixed")), "the native mate anchor is floating")
    for request in case["mates"]:
        author.get(model, "ClearSelection2", True)
        for position, (occurrence, plane) in enumerate(request["planes"]):
            selection = f"{plane}@{names[occurrence]}@{title}"
            require(bool(author.get(extension, "SelectByID2", selection, "PLANE", 0.0, 0.0, 0.0,
                                    position > 0, 1, Swapp.nothing(), 0)),
                    f"the native mate plane could not be selected: {selection}")
        kind = TYPES[request["kind"]]
        distance = request.get("distance_m", 0.0)
        error_status = Swapp.byref_long()
        mate = author.get(assembly, "AddMate5", kind, 0, False, distance, distance, distance,
                          1.0, 1.0, 0.0, 0.0, 0.0, False, False, 0, error_status)
        require(mate is not None and int(error_status.value) == 1,
                f"the native mate was rejected with status {error_status.value}")
    author.get(model, "ClearSelection2", True)


def mate_features(author, model):
    feature = author.get(model, "FirstFeature")
    for _ in range(256):
        require(feature is not None, "the native mate group is missing")
        if author.get(feature, "GetTypeName2") == "MateGroup":
            break
        feature = author.get(feature, "GetNextFeature")
    else:
        raise ValueError("native feature traversal exceeded its bound")
    child = author.get(feature, "GetFirstSubFeature")
    while child is not None:
        yield child
        child = author.get(child, "GetNextSubFeature")


def mate_endpoint(author, mate, index):
    entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
    occurrence = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
    reference_type = int(author.get(entity, "ReferenceType2"))
    parameters = [float(value) for value in author.get(entity, "EntityParams")]
    require(reference_type == 3 and len(parameters) == 8 and all(map(math.isfinite, parameters)),
            "the native mate entity does not describe a plane")
    return {"occurrence": str(author.get(occurrence, "Name2")), "reference_type": reference_type,
            "point": parameters[:3], "normal": parameters[3:6]}


def require_plane(endpoint, transform, plane_name):
    axis = PLANE_AXES[plane_name]
    normal = transform[axis * 3:axis * 3 + 3]
    cosine = math.fsum(left * right for left, right in zip(normal, endpoint["normal"], strict=True))
    displacement = math.fsum(normal[index] * (endpoint["point"][index] - transform[9 + index])
                             for index in range(3))
    require(math.isclose(abs(cosine), 1.0, abs_tol=1e-10) and abs(displacement) <= 1e-10,
            f"the mate endpoint differs from its occurrence's {plane_name}")


def observe_plane_mates(author, model, occurrences, case):
    require([row["placement_index"] for row in occurrences if row["fixed"]] == [case["fixed_occurrence"]],
            "the persisted assembly has the wrong fixed occurrence")
    by_name = {row["name"]: row for row in occurrences}
    pending = list(case["mates"])
    rows = []
    for feature in mate_features(author, model):
        require(pending, "the native assembly has an unexpected additional mate")
        mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
        require(int(author.get(mate, "GetMateEntityCount")) == 2, "expected two native mate endpoints")
        kind = int(author.get(mate, "Type"))
        alignment = int(author.get(mate, "Alignment"))
        endpoints = [mate_endpoint(author, mate, index) for index in range(2)]
        endpoint_names = {endpoint["occurrence"] for endpoint in endpoints}
        matches = [request for request in pending if TYPES[request["kind"]] == kind and
                   {occurrences[index]["name"] for index, _ in request["planes"]} == endpoint_names]
        require(len(matches) == 1 and alignment == 0, "the native mate type, alignment or participant set differs")
        request = matches[0]
        pending.remove(request)
        planes = {occurrences[index]["name"]: name for index, name in request["planes"]}
        for endpoint in endpoints:
            component = by_name[endpoint["occurrence"]]
            require_plane(endpoint, component["transform"], planes[endpoint["occurrence"]])
        row = {"name": str(author.get(feature, "Name")), "type": kind, "alignment": alignment, "entities": endpoints}
        if request["kind"] == "distance":
            display = author.get(feature, "GetFirstDisplayDimension")
            require(display is not None, "native distance mate has no display dimension")
            parameter = author.get(display, "GetDimension2", 0)
            value = float(author.get(parameter, "SystemValue"))
            require(math.isclose(value, request["distance_m"], rel_tol=0.0, abs_tol=1e-12),
                    "native mate distance differs from the authored design")
            row["dimension_m"] = value
            row["dimension_name"] = str(author.get(parameter, "FullName"))
            row["flipped"] = bool(author.get(mate, "Flipped"))
        rows.append(row)
    require(not pending, "the native mate group is missing an authored mate")
    return rows
