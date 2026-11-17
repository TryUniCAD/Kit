from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from Core import Obj
from builders.AssemblyOccurrences import mate_occurrence_component
from builders.Definition import identity_transform
from builders.Metadata import integer
from builders.Model import component_plane, logged_creation_time
from builders.Part import PartConstruction
from builders.Sketch import PlaneFrame, frame_transform


@dataclass(frozen=True)
class PlanarMateEndpoint:
    component_plane: Obj
    resolved_geometry: dict
    detached_geometry: dict


def _xyz(value):
    return tuple(value[key] for key in "xyz")


def _point(value):
    return dict(zip("xyz", value, strict=True))


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
    update = integer(occurrence["f3e0"], "child update stamp")
    signed_update = update if update < 0x80000000 else update - 0x100000000
    resolved = {
        "f08": signed_update,
        "f10": dict(placement), "f18": dict(placement),
        "fd0": origin, "fe8": normal, "f100": frame_transform(frame=frame),
        **dict(zip(extent_keys, bounds, strict=True)),
    }
    detached = {"fd0": dict(origin), "fe8": dict(normal), "f100": identity_transform(),
                **dict.fromkeys(extent_keys, 0.0)}
    return PlanarMateEndpoint(selected, resolved, detached)
