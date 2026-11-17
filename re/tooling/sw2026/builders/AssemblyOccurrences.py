from __future__ import annotations

from collections.abc import Iterable, Sequence
from itertools import product
from math import isfinite, sqrt

from Core import Obj
from builders.Assembly import _initial_component_configuration, bounding_box, ordinary_part_reference_stamps
from builders.AssemblyTargetState import target_update_stamps
from builders.ExternalFiles import referenced_configuration
from builders.Metadata import integer
from builders.Model import PersistentIds, feature
from builders.Sketch import PlaneFrame


def _shared_file(record: Obj, *, kind: int) -> dict:
    if not isinstance(record, Obj) or record.cls != "moExtObject_c":
        raise ValueError("ordinary occurrences require a native external file record")
    definition = record["shared"]
    if definition["f20"] != kind or definition["f08"]:
        raise ValueError("ordinary occurrences require a nonvirtual file of the expected kind")
    return definition


def _file_identity(definition: dict) -> tuple:
    return (definition["h18"]["f08"], definition["h10"]["f08"], definition["f20"], definition["f28"])


def _configuration_pair(configuration: Obj, *, owner: Obj, kind: str) -> dict:
    if not isinstance(configuration, Obj) or configuration.cls != kind or configuration["owner"] is not owner:
        raise ValueError("the selected configuration must belong to the referenced document")
    return referenced_configuration(name=configuration["f18"]["f08"], local_id=configuration["f08"])


def _external_feature(*, reference: Obj, owner_file: dict, backlink: bool) -> Obj:
    return Obj("moExtFeature_c", {
        "f10": owner_file,
        "f18": referenced_configuration(name=None, local_id=None),
        "f38": Obj("moCStringHandle_c", {"f08": reference["f18"]["f08"]}),
        "f40": 0,
        "f44": reference["f08"],
        "f50": reference if backlink else None,
        "f58": -1,
    })


def _placement_transform(frame: PlaneFrame) -> dict:
    matrix = (*frame.u, *frame.v, *frame.normal)
    identity = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    x, y, z = frame.origin
    result = {"has_matrix": int(matrix != identity), "f58": x, "f60": y, "f68": z, "f70": 1.0, "f78": 0}
    if result["has_matrix"]:
        result["f08"] = {f"m{index}": value for index, value in enumerate(matrix)}
    return result


def _transform_point(frame: PlaneFrame, point: Sequence[float]) -> tuple[float, ...]:
    x, y, z = point
    return tuple(origin + x * u + y * v + z * w for origin, u, v, w in zip(frame.origin, frame.u, frame.v, frame.normal, strict=True))


def placed_occurrence_bounds(*, reference: Obj, placement: PlaneFrame) -> dict:
    local = reference["f370"]
    corners = tuple(product(*((local[f"b{index + 6}"], local[f"b{index + 3}"]) for index in range(3))))
    coordinates = tuple(zip(*(_transform_point(placement, point) for point in corners), strict=True))
    center = _transform_point(placement, tuple(local[f"b{index}"] for index in range(3)))
    values = (*center, *(max(axis) for axis in coordinates), *(min(axis) for axis in coordinates), local["b9"])
    if not all(isfinite(value) for value in values):
        raise ValueError("derived occurrence bounds exceed the archive numeric domain")
    return {f"b{index}": value for index, value in enumerate(values)}


def _union_placed_bounds(left: dict, right: dict) -> dict:
    low = tuple(min(right[key], left[key]) for key in ("b6", "b7", "b8"))
    high = tuple(max(right[key], left[key]) for key in ("b3", "b4", "b5"))
    center = tuple(left[key] for key in ("b0", "b1", "b2"))
    incoming_center = tuple(right[key] for key in ("b0", "b1", "b2"))
    dx, dy, dz = (b - a for a, b in zip(center, incoming_center, strict=True))
    distance = sqrt(dx * dx + dy * dy + dz * dz)
    radius, incoming_radius = left["b9"], right["b9"]
    enclosing_radius = (radius + incoming_radius + distance) * 0.5
    if not isfinite(enclosing_radius):
        raise ValueError("derived assembly bounds exceed the archive numeric domain")
    if enclosing_radius > radius:
        if enclosing_radius <= incoming_radius:
            center, radius = incoming_center, incoming_radius
        else:
            weight = (enclosing_radius - radius) / distance
            center = tuple(value + change * weight for value, change in zip(center, (dx, dy, dz), strict=True))
            radius = enclosing_radius
            x, y, z = (max(abs(a - c), abs(b - c)) for a, b, c in zip(low, high, center, strict=True))
            corner_squared = x * x + y * y + z * z
            radius_squared = radius * radius
            if corner_squared + 5e-9 < radius_squared or (radius > 1e-10 and corner_squared * 1.000000005 < radius_squared):
                return bounding_box(minimum=low, maximum=high)
    values = (*center, *high, *low, radius)
    if not all(isfinite(value) for value in values):
        raise ValueError("derived assembly bounds exceed the archive numeric domain")
    return {f"b{index}": value for index, value in enumerate(values)}


def assembly_occurrence_bounds(*, occurrences: Iterable[tuple[Obj, PlaneFrame]]) -> dict:
    boxes = (placed_occurrence_bounds(reference=reference, placement=placement) for reference, placement in occurrences)
    result = next(boxes, None)
    if result is None:
        raise ValueError("populated assembly bounds require at least one occurrence")
    for box in boxes:
        result = _union_placed_bounds(result, box)
    return result


def _resolved_occurrence(
    *,
    owner: Obj,
    owner_file: Obj,
    child_model: Obj,
    child_header: Obj,
    child_configuration: Obj,
    child_file: Obj,
    name: str,
    placement: PlaneFrame,
    kind: int,
    local_bounds: dict,
    stamps: dict,
    feature_ordinal: int,
    allocator: PersistentIds,
    date_code: int,
    parasolid_version: int,
) -> Obj:
    if not isinstance(owner, Obj) or owner.cls != "moAssembly_c":
        raise ValueError("a resolved occurrence requires an ordinary assembly owner")
    if not isinstance(placement, PlaneFrame):
        raise ValueError("a resolved occurrence requires an explicit rigid placement")
    if not isinstance(allocator, PersistentIds):
        raise ValueError("a resolved occurrence requires the assembly's persistent id allocator")
    feature_ordinal = integer(feature_ordinal, "unified feature ordinal", low=1, high=0x7FFFFFFF)
    owner_definition = _shared_file(owner_file, kind=3)
    if owner_definition["h10"]["f08"] != owner["f18"]["f08"]:
        raise ValueError("the containing file must describe the generated assembly")
    child_definition = _shared_file(child_file, kind=kind)
    selection = _configuration_pair(child_configuration, owner=child_model, kind="moPartConfiguration_c" if kind == 2 else "moConfiguration_c")
    child_self = _shared_file(child_header["f38"], kind=kind)
    if _file_identity(child_definition) != _file_identity(child_self):
        raise ValueError("the child directory record must describe the generated child file")
    reference = feature(
        cls="moReference_c", name=name, owner=owner, allocator=allocator,
        date_code=date_code, parasolid_version=parasolid_version,
    )
    reference.f["f0c"] &= 0xFFFD7FF8
    reference.f.update(stamps)
    reference.f.update({name: 0 for name in (
        "has_discarded_xform", "has_f378", "f388", "f408", "f418", "f41c", "f450", "f454",
        "f458", "f49c", "f4a0", "f4c0", "f4d8", "f4dc", "f4f0", "f524", "f530", "f550", "f368",
    )})
    reference.f.update({name: None for name in (
        "f468", "f470", "f488", "f490", "f538", "f548", "discarded_stack",
    )})
    reference.f.update({
        "has_f360": 1,
        "f360": _placement_transform(placement),
        "has_f370": 1,
        "f370": local_bounds,
        "f3b0": child_file,
        "f3c0": selection,
        "f3dc": -1,
        "f400": 3,
        "f4a4": -1,
        "f4b0": -1,
        "f4b4": feature_ordinal,
        "f4f8": _external_feature(reference=reference, owner_file=owner_definition, backlink=True),
        "f500": "",
        "f508": "",
        "f55c": 101,
    })
    return reference


def resolved_part_occurrence(*, minimum: Sequence[float], maximum: Sequence[float], child_model: Obj, child_header: Obj, **values) -> Obj:
    stamps = ordinary_part_reference_stamps(child_model=child_model, child_header=child_header, assigned_transform=True)
    return _resolved_occurrence(child_model=child_model, child_header=child_header, kind=2,
                                local_bounds=bounding_box(minimum=minimum, maximum=maximum), stamps=stamps, **values)


def resolved_assembly_occurrence(*, child_model: Obj, child_header: Obj, **values) -> Obj:
    if not isinstance(child_model, Obj) or child_model.cls != "moAssembly_c" or child_model["has_f1a18"] != 1:
        raise ValueError("a subassembly occurrence requires its generated populated model and local bounds")
    if not isinstance(child_header, Obj) or child_header.cls != "moHeader_c":
        raise ValueError("a subassembly occurrence requires its generated model header")
    geometry, transform = target_update_stamps(child_model)
    stamps = {"f3e0": integer(child_header["f40"], "target update stamp"), "f3e8": integer(child_header["f48"], "target modification time"),
              "f3f0": 102, "f3f4": geometry, "f3f8": transform}
    return _resolved_occurrence(child_model=child_model, child_header=child_header, kind=3,
                                local_bounds=dict(child_model["f1a18"]), stamps=stamps, **values)


def occurrence_path(*, target: Obj) -> Obj:
    if not isinstance(target, Obj) or target.cls != "moExtFeature_c":
        raise ValueError("an ordinary occurrence path requires its external-feature entry")
    return Obj("moReferenceChain_c", {
        "f08": Obj("moExtFeatureList_c", {"n": 1, "f08": [{"o": target}]}),
        "f20": 0,
        "f24": 0,
        "f40": referenced_configuration(name=None, local_id=None),
    })


def occurrence_chain_stamp(reference: Obj) -> int:
    return (101 + reference["f3f0"]) & 0xFFFFFFFF


def mate_occurrence_component(*, owner: Obj, reference: Obj) -> Obj:
    if not isinstance(reference, Obj) or reference.cls != "moReference_c":
        raise ValueError("a mate endpoint requires an ordinary resolved occurrence")
    if not isinstance(owner, Obj) or owner.cls != "moAssembly_c":
        raise ValueError("a mate occurrence path requires the containing assembly")
    if not any(row["o"] is reference for row in owner["f68"]["list"]["items"]):
        raise ValueError("the selected occurrence must be a member of the containing assembly")
    target = reference["f4f8"]
    if not isinstance(target, Obj) or target.cls != "moExtFeature_c":
        raise ValueError("a mate occurrence path requires its external-feature entry")
    if target["f50"] is not reference or target["f44"] != reference["f08"]:
        raise ValueError("a mate occurrence path must retain the containing assembly and occurrence backlink")
    return Obj("moChainComponent_c", {
        "owner": owner,
        "f20": occurrence_path(target=target),
        "f30": occurrence_chain_stamp(reference),
    })


def occurrence_configuration(
    *,
    reference: Obj,
    configuration: Obj,
    display_state: tuple[str, int] | None = None,
) -> Obj:
    if not isinstance(reference, Obj) or reference.cls != "moReference_c":
        raise ValueError("occurrence configuration requires its native occurrence")
    assembly_configuration = _configuration_pair(configuration, owner=reference["owner"], kind="moConfiguration_c")
    owner_file = reference["f4f8"]["f10"]
    target = _external_feature(reference=reference, owner_file=owner_file, backlink=False)
    path = occurrence_path(target=target)
    context_file = Obj("moExtObject_c", {
        "shared": owner_file,
        "f48": 0,
        "f4c": 1,
        "f50": 0,
        "f54": 0,
        "f58": 0,
        "f60": 0,
        "f70": 0,
        "f78": -1,
        "refcfg": assembly_configuration,
    })
    component = Obj("moContextChainComponent_c", {
        "owner": None,
        "f20": path,
        "f30": occurrence_chain_stamp(reference),
        "f40": context_file,
        "f48": 0,
    })
    child_kind = reference["f3b0"]["shared"]["f20"]
    if child_kind not in (2, 3):
        raise ValueError("occurrence configuration requires an ordinary external part or assembly")
    selected_options = configuration["fc48" if child_kind == 3 else "fc50"]
    if not isinstance(selected_options, Obj) or selected_options.cls != "moConfig_c":
        raise ValueError("ordinary occurrence configuration requires the assembly insertion options")
    options = Obj("moConfig_c", dict(selected_options.f))
    options["f64"] = 0
    result = _initial_component_configuration()
    result.f.update(f08=options, f10=component, f28=dict(reference["f3c0"]))
    if display_state is not None:
        if not isinstance(display_state, tuple) or len(display_state) != 2:
            raise ValueError("a child display state requires a name and local id")
        state = referenced_configuration(name=display_state[0], local_id=display_state[1])
        if state["f10"] < 0:
            raise ValueError("an explicit child display state must select an actual entry")
        options.f.update(f48=state["f08"], f50=state["f10"])
        result["f18"] |= 0x100000
    return result
