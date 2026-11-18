from copy import deepcopy
from dataclasses import replace

from OriginalPlanarNames import PLANES, require
from SdkPlanarGroupPrediction import predict, transform


COMMON_CHILD_M = (.04, .02, .01)
EDIT_INCREMENT_M = .01573


def dimensioned_child(name, dimensions, configuration_name):
    from interchange.Enums.EnumValues import ValueKind
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

    document = MakePlainDoc(name, *(value * 1000 for value in dimensions))
    sketch, = document.sketches
    parameters = tuple(Parameter(f"parameter/{role}", f"D{index + 1}", ParameterValue(length * 1000, ValueKind.KLength, "mm"), owner_id=sketch.id) for index, (role, length) in enumerate(zip(("width", "height"), dimensions[:2], strict=True)))
    axes = tuple(SketchRelation(f"relation/axis/{index}", "horizontal" if index % 2 == 0 else "vertical", (ConstraintRef(row.id),)) for index, row in enumerate(sketch.entities))
    lengths = tuple(SketchRelation(f"relation/length/{index}", "distance", (ConstraintRef(sketch.entities[index].id, "start"), ConstraintRef(sketch.entities[index].id, "end")), parameter.id) for index, parameter in enumerate(parameters))
    sketch = replace(sketch, constraints=(*axes, *lengths), parameter_ids=tuple(row.id for row in parameters))
    return replace(document, sketches=(sketch,), parameters=(*parameters, document.parameters[0]), configurations=(replace(document.configurations[0], name=configuration_name),))


def apply_names(system, names):
    require({kind for kind, _ in system["folders"]} == set(names["folder_names"]), "the source ordinary folder role set exceeds the measured constructor")
    system["folders"] = [[kind, names["folder_names"][kind]] for kind, _ in system["folders"]]
    system.update({key: names[key] for key in ("planes", "cabinet_name", "origin_name")})
    if "mate_group_name" in names:
        system["mate_group_name"] = names["mate_group_name"]


def translate(case, names, output, dimensions=COMMON_CHILD_M):
    from interchange.serialization.EncodeData import ToData
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmInput import MakeAsmInput
    from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import BlindCaseInput

    require(set(case) <= {"name", "split", "placements", "fixed_occurrence", "mates"} and {"name", "placements", "fixed_occurrence", "mates"} <= set(case), "the original source recipe has unqualified case state")
    require(set(output) == {"assembly_path", "child_path"}, "the evaluation requires explicit separate generated file identities")
    require(names["schema"] == "kit.sw2026.original-planar-authored-names.v1" and names["child"]["sketch_name"] == "Sketch1" and names["child"]["boss_name"] == "Boss-Extrude1", "the source semantic name projection exceeds the measured child role profile")
    require(len(names["occurrence_names"]) == len(case["placements"]) and len(names["mate_names"]) == len(case["mates"]), "the recipe and complete source name projection disagree")
    child_name = "CohortChild"
    assembly = MakeAsmInput(case["name"], False)["assembly"]
    assembly["configuration_name"] = names["assembly"]["configuration_name"]
    assembly["output"]["path_name"] = output["assembly_path"]
    apply_names(assembly["system"], names["assembly"]["system"])
    child = BlindCaseInput(child_name, False)
    child["document"] = ToData(dimensioned_child(child_name, dimensions, names["child"]["configuration_name"]))
    child["settings"]["output"]["path_name"] = output["child_path"]
    apply_names(child["settings"]["system"], names["child"]["system"])
    width, height, _ = dimensions
    child["rectangle_dimensions"] = {"width_text_m": [-width * .15, -height / 2 - .0067], "height_text_m": [width / 2 + .0082, height * .11], "route_centerline": False}
    occurrences = []
    for name, placement in zip(names["occurrence_names"], case["placements"], strict=True):
        require(set(placement) == {"axis", "angle_deg", "translation_m"}, "the original placement recipe has unsupported state")
        matrix = transform(placement)
        occurrences.append({"name": name, "origin": list(placement["translation_m"]), "u": matrix[:3], "v": matrix[3:6]})
    native = deepcopy(case)
    mates = []
    for name, row in zip(names["mate_names"], native["mates"], strict=True):
        require(set(row) <= {"name", "kind", "planes", "distance_m"} and {"kind", "planes"} <= set(row) and row["kind"] in ("coincident", "parallel", "distance") and len(row["planes"]) == 2, "the original mate recipe has unsupported authored state")
        row["name"] = name
        endpoints = []
        for index, datum in row["planes"]:
            require(type(index) is int and 0 <= index < len(occurrences) and datum in PLANES.values(), "an original recipe endpoint does not select an actual occurrence and principal datum")
            endpoints.append({"occurrence": index, "axis": next(axis for axis, plane in PLANES.items() if plane == datum)})
        mate = {"kind": row["kind"], "name": name, "endpoints": endpoints}
        if row["kind"] == "distance":
            mate.update(distance_m=row["distance_m"], design_intent=False, selected_leader=0)
        else:
            require("distance_m" not in row, "a nondimensional source recipe contains an unsupported length")
        mates.append(mate)
    request = {"assembly": assembly, "child": child, "occurrences": occurrences, "mates": mates, "fixed_occurrence": case["fixed_occurrence"]}
    distances = [row["distance_m"] for row in native["mates"] if row["kind"] == "distance"]
    require(len(distances) == 1, "the original evaluation requires one actual positive driving distance")
    prediction = predict(request, native, distances[0] + EDIT_INCREMENT_M)
    return request, prediction
