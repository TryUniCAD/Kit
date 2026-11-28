from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import GroupMateIn
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.PlaneEndIn import PlaneEndIn
from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import DistanceInput


def group_settings(values):
    result = []
    for row in values:
        expected = {"kind", "name", "endpoints"} | ({"distance_m", "design_intent", "selected_leader"} if row["kind"] == "distance" else set())
        if set(row) != expected or any(set(value) != {"occurrence", "axis"} for value in row["endpoints"]):
            raise ValueError("planar group intent contains an unsupported or missing endpoint or dimension field")
        distance = DistanceInput(row["distance_m"], row["design_intent"], row["selected_leader"]) if row["kind"] == "distance" else None
        ends = tuple(PlaneEndIn(value["occurrence"], value["axis"]) for value in row["endpoints"])
        if len(ends) != 2:
            raise ValueError("each planar mate requires exactly two actual endpoint selections")
        result.append(GroupMateIn(row["kind"], row["name"], (ends[0], ends[1]), distance))
    return tuple(result)
