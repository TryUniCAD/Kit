from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from Core import Obj
from builders.AssemblyOccurrences import mate_occurrence_component
from builders.Definition import identity_transform
from builders.Metadata import integer
from builders.Model import absolute_reference_plane, component_plane, logged_creation_time, reference_wrapper_fields, unregistered_plane_reference
from builders.Part import PartConstruction
from builders.Sketch import PlaneFrame, frame_transform


@dataclass(frozen=True)
class PlanarMateEndpoint:
    component_plane: Obj
    resolved_geometry: dict
    detached_geometry: dict
    configuration_id: int


def _xyz(value):
    return tuple(value[key] for key in "xyz")


def _point(value):
    return dict(zip("xyz", value, strict=True))


def _signed_update(value: int) -> int:
    update = integer(value, "model update stamp")
    return update if update < 0x80000000 else update - 0x100000000


def _placed_plane(datum: Obj, placement: dict) -> PlaneFrame:
    if placement["f70"] != 1.0 or placement["f78"] != 0:
        raise ValueError("a planar mate endpoint requires a rigid ordinary occurrence transform")
    if placement["has_matrix"]:
        matrix = placement["f08"]
        columns = tuple(tuple(matrix[f"m{row * 3 + axis}"] for row in range(3)) for axis in range(3))
    else:
        columns = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    translation = tuple(placement[key] for key in ("f58", "f60", "f68"))

    def rotate(vector):
        return tuple(sum(a * b for a, b in zip(vector, column, strict=True)) for column in columns)

    root = rotate(_xyz(datum["f6f8"]["root"]))
    origin = tuple(a + b for a, b in zip(translation, root, strict=True))
    return PlaneFrame(origin=origin, u=rotate(datum["_plane_u"]), v=rotate(datum["_plane_v"]))


def _datum_creation_time(child: PartConstruction, datum: Obj) -> int:
    logs = child.model_header["f20"]["items"]
    log = next((row["o"] for row in logs if row["o"]["f48"] == datum["f08"]), None)
    stamps = () if log is None else (row["o"]["f18"] for row in log["items"])
    return logged_creation_time(timestamps=stamps)


def planar_mate_endpoint(*, assembly: Obj, occurrence: Obj, child: PartConstruction, datum: Obj, created_at: int | None = None) -> PlanarMateEndpoint:
    if not isinstance(child, PartConstruction) or child.model.cls != "moPart_c":
        raise ValueError("a planar mate endpoint requires a constructed native part")
    if not isinstance(datum, Obj) or datum.cls != "moRefPlane_c" or datum.get("_principal_axis") not in ("x", "y", "z"):
        raise ValueError("the endpoint must select a generated principal datum plane")
    if datum["owner"] is not child.model or not any(datum is node for node in child.features):
        raise ValueError("the selected plane must belong to the actual referenced part")
    chain = mate_occurrence_component(owner=assembly, reference=occurrence)
    if not isinstance(child.model_header["f38"], Obj):
        raise ValueError("the referenced part requires a generated file identity")
    reference = occurrence["f3b0"]["shared"]
    child_file = child.model_header["f38"]["shared"]
    identity = ("h10", "h18")
    if any(reference[key]["f08"] != child_file[key]["f08"] for key in identity):
        raise ValueError("the child file identity differs from the selected occurrence")
    selected_configuration = occurrence["f3c0"]
    if (selected_configuration["f10"] != child.configuration["f08"]
            or selected_configuration["f08"] != child.configuration["f18"]["f08"]
            or occurrence["f3e0"] != child.model_header["f40"]):
        raise ValueError("the mate occurrence must target the current child configuration and update")

    creation_time = _datum_creation_time(child, datum)
    if created_at is not None and (type(created_at) is not int or created_at != creation_time):
        raise ValueError("the selected datum creation time must match the referenced child's log")
    datum_geometry = datum["f6f8"]
    selected = component_plane(
        plane=datum, component=child.model["f990"], created_at=creation_time,
        principal_normal=_xyz(datum_geometry["normal"]),
    )
    selected["f58"] = chain
    placement = occurrence["f360"]
    frame = _placed_plane(datum, placement)
    extent_keys = ("fb0", "fb8", "fc0", "fc8")
    bounds = tuple(datum_geometry[f"b{index}"] for index in range(4))
    if not all(isfinite(value) for value in bounds) or bounds[0] < bounds[1] or bounds[2] < bounds[3]:
        raise ValueError("the datum display rectangle must contain finite ordered bounds")
    origin = _point(frame.origin)
    normal = _point(frame.normal)
    resolved = {
        "f08": _signed_update(occurrence["f3e0"]),
        "f10": dict(placement), "f18": dict(placement),
        "fd0": origin, "fe8": normal, "f100": frame_transform(frame=frame),
        **dict(zip(extent_keys, bounds, strict=True)),
    }
    detached = {"fd0": dict(origin), "fe8": dict(normal), "f100": identity_transform(),
                **dict.fromkeys(extent_keys, 0.0)}
    return PlanarMateEndpoint(selected, resolved, detached, child.configuration["f08"])


def resolved_planar_wrapper(*, endpoint: PlanarMateEndpoint) -> Obj:
    values = reference_wrapper_fields(reference=endpoint.component_plane)
    values.update(endpoint.resolved_geometry)
    values.update({
        "f68": 1, "has_f10": 1, "has_f18": 1, "f0c": endpoint.configuration_id,
        "f188": _point((0.0, 0.0, 0.0)),
    })
    return Obj("moPlaneRef_w", values)


def detached_planar_wrapper(*, endpoint: PlanarMateEndpoint, model_header: Obj, configuration: Obj,
                            date_code: int, parasolid_version: int) -> Obj:
    owner = endpoint.component_plane["f58"]["owner"]
    geometry = endpoint.detached_geometry
    if model_header.cls != "moHeader_c" or not model_header["fec"] or configuration.cls != "moConfiguration_c":
        raise ValueError("detached plane wrappers require the assembly model header and configuration")
    plane = absolute_reference_plane(
        owner=owner, name=None, root=geometry["fd0"], normal=geometry["fe8"], transform=identity_transform(),
        bounds=(0.0, 0.0, 0.0, 0.0), date_code=date_code, parasolid_version=parasolid_version,
    )
    component = unregistered_plane_reference(plane=plane, component=owner["f990"])
    component["f9c"] = endpoint.component_plane["ff0"]["f00"]
    values = reference_wrapper_fields(reference=component)
    values.update(geometry)
    values.update({
        "f08": _signed_update(model_header["f40"]), "f0c": configuration["f08"],
        "f68": 1, "f188": _point((0.0, 0.0, 0.0)),
    })
    return Obj("moPlaneRef_w", values)


def register_planar_wrapper_ids(*, mate: Obj) -> None:
    if not isinstance(mate, Obj) or mate.cls != "moMateCoincident":
        raise ValueError("reference allocation requires an ordinary coincident mate")
    group = mate.get("owner")
    if not isinstance(group, Obj) or group.cls != "moMateGroup_c":
        raise ValueError("reference allocation requires the registered mate group")
    assembly = group.get("owner")
    if not isinstance(assembly, Obj) or assembly.cls != "moAssembly_c":
        raise ValueError("the mate group must belong to the actual assembly")
    mate_id = integer(mate["f08"], "mate persistent ID", high=0x7FFFFFFE)
    counter = integer(assembly["fd48"], "assembly wrapper counter", high=0x7FFFFFFF)
    wrappers = tuple(row["o"] for row in mate["f410"])
    if len(wrappers) != 2 or wrappers[0] is wrappers[1]:
        raise ValueError("a coincident mate requires two distinct resolved wrappers")
    assignments = []
    used = set()
    for ordinal, wrapper in enumerate(wrappers):
        if not isinstance(wrapper, Obj) or wrapper.cls != "moPlaneRef_w" or wrapper["f60"] is not None:
            raise ValueError("only ordinary resolved plane wrappers consume these reference IDs")
        chain = wrapper["f58"]["f58"]
        if chain.cls != "moChainComponent_c" or chain["owner"] is not assembly:
            raise ValueError("the wrapper chain must bind the containing assembly")
        reference_id = wrapper["f78"]
        if reference_id == -12345:
            reference_id = integer(counter, "next assembly wrapper ID", high=0x7FFFFFFE)
            counter += 1
        else:
            integer(reference_id, "allocated assembly wrapper ID", high=assembly["fd48"] - 1)
        if reference_id in used:
            raise ValueError("distinct mate wrappers cannot share a reference ID")
        used.add(reference_id)
        assignments.append((wrapper, reference_id, ordinal))
    for wrapper, reference_id, ordinal in assignments:
        wrapper.f.update(f74=mate_id, f78=reference_id, f7c=ordinal)
    assembly["fd48"] = counter
