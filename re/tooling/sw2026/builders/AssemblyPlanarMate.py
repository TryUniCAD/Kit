from __future__ import annotations

from Core import Obj
from builders.AssemblyMateEndpoint import detached_planar_wrapper, planar_mate_endpoint, register_planar_wrapper_ids, resolved_planar_wrapper
from builders.Metadata import fields, integer, sequence
from builders.Model import feature_filetime, model_feature


def _selected_endpoints(*, assembly, occurrences, child, selections):
    choices = tuple(sequence(selections, "coincident mate selections"))
    if len(choices) != 2:
        raise ValueError("a coincident plane mate requires two selections")
    datums = {node["f18"]["f08"]: node for node in child.features if node.get("_principal_axis")}
    endpoints = []
    positions = set()
    for choice in choices:
        selected = fields(choice, "coincident mate selection", ("occurrence", "datum"))
        position = integer(selected["occurrence"], "mate occurrence ordinal", high=len(occurrences) - 1)
        datum = datums.get(selected["datum"])
        if datum is None or position in positions:
            raise ValueError("the coincident mate must select actual planes on two distinct occurrences")
        positions.add(position)
        endpoints.append(planar_mate_endpoint(assembly=assembly, occurrence=occurrences[position], child=child, datum=datum))
    return endpoints


def coincident_planar_mate(*, assembly, group, occurrences, child, model_header, configuration, allocator, target, request, created_at) -> Obj:
    fields(request, "coincident plane mate", ("kind", "name", "alignment", "fixed_occurrence", "endpoints"), ("created_at",))
    if request["kind"] != "coincident" or request["alignment"] != "aligned" or len(occurrences) != 2:
        raise ValueError("the discovery composer admits one aligned coincident mate between two ordinary occurrences")
    if group.cls != "moMateGroup_c" or group["owner"] is not assembly:
        raise ValueError("the coincident mate must register with the assembly's own mate group")
    filetime = feature_filetime(created_at)
    fixed = integer(request["fixed_occurrence"], "fixed occurrence ordinal", high=len(occurrences) - 1)
    endpoints = _selected_endpoints(assembly=assembly, occurrences=occurrences, child=child, selections=request["endpoints"])
    resolved = [{"o": resolved_planar_wrapper(endpoint=endpoint)} for endpoint in endpoints]
    detached = [
        {"k": index, "o": detached_planar_wrapper(endpoint=endpoint, model_header=model_header, configuration=configuration, **target)}
        for index, endpoint in enumerate(endpoints)
    ]
    mate = model_feature(cls="moMateCoincident", name=request["name"], owner=group, allocator=allocator, **target)
    mate.f.update({
        **filetime,
        "f370": [], "f388": 0, "f390": 0, "f394": 0,
        "f3b4": 1, "f3b8": 0, "has_f3c0": 0, "f3c0": None,
        "f3c8": detached, "f410": resolved,
        "f430": None, "f438": 0, "f448": [], "f468": None, "f470": None, "f478": None,
        "f480": 0, "f488": "", "f490": "",
    })
    register_planar_wrapper_ids(mate=mate)
    occurrences[fixed]["f408"] = 1
    return mate
