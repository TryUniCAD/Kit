from __future__ import annotations

from collections.abc import Sequence
from math import isfinite, sqrt

from AssemblyMates import store_mate_list
from Core import Obj
from builders.ExternalFiles import referenced_configuration
from builders.Metadata import FILE_VERSION
from builders.Model import PersistentIds, base_configuration_fields, clear_model_update, component_plane, detail_cabinet, folder, logged_creation_time, model_feature, model_fields, object_list, principal_planes, relation_manager, unit_component
from builders.Sketch import PlaneFrame, origin_profile


PLANAR_MATE_CLASSES = {"coincident": "moMateCoincident", "parallel": "moMateParallel"}


def bounding_box(*, minimum: Sequence[float], maximum: Sequence[float]) -> dict:
    points = []
    for name, point in (("minimum", minimum), ("maximum", maximum)):
        if not isinstance(point, Sequence) or isinstance(point, (str, bytes, bytearray)) or len(point) != 3:
            raise ValueError(f"{name} must contain three coordinates in native model space")
        if any(type(value) not in (int, float) for value in point):
            raise ValueError(f"{name} coordinates must be real numbers")
        try:
            values = tuple(float(value) for value in point)
        except OverflowError as error:
            raise ValueError(f"{name} coordinates exceed the archive numeric domain") from error
        if not all(isfinite(value) for value in values):
            raise ValueError(f"{name} coordinates must be finite")
        points.append(values)
    low, high = points
    if any(a > b for a, b in zip(low, high, strict=True)):
        raise ValueError("minimum coordinates must not exceed maximum coordinates")
    center = tuple((a + b) * 0.5 for a, b in zip(low, high, strict=True))
    dx, dy, dz = (b - a for a, b in zip(low, high, strict=True))
    radius = sqrt(dx * dx + dy * dy + dz * dz) * 0.5
    values = (*center, *high, *low, radius)
    if not all(isfinite(value) for value in values):
        raise ValueError("derived bounding-box state exceeds the archive numeric domain")
    return {f"b{index}": value for index, value in enumerate(values)}


def _initial_configuration_options() -> Obj:
    fields = {name: 0 for name in (
        "f14", "f28", "f20", "f34", "f40", "f58", "f5c", "f60",
        "f68", "f6c", "f70", "f74",
    )}
    fields.update({
        "f08": 2, "f0c": 1, "f10": 1, "f18": 2,
        "f38": 6, "f3c": 1, "f48": "", "f50": -1, "f64": -1,
    })
    return Obj("moConfig_c", fields)


def _initial_component_configuration() -> Obj:
    return Obj("moConfigObject_c", {
        "f08": _initial_configuration_options(),
        "f10": None,
        "f28": referenced_configuration(name=None, local_id=None),
        "f40": None,
        "f48": {"f08": object_list(), "f28": 101},
        "has_f140": 0,
        "f78": object_list(),
        "f18": 0x111,
        "f20": 0,
        "f148": 0,
        "has_f170": 0,
        "fc0": None,
        "fc8": None,
        "f178": "",
        "f190": 0,
        "f118": object_list(),
        "fd0": object_list(),
    })


def initial_configuration(
    *,
    name: str,
    owner: Obj,
    local_id: int,
    date_code: int,
    parasolid_version: int,
    updated_at: int,
    description: str = "",
) -> Obj:
    result = Obj("moConfiguration_c")
    fields = base_configuration_fields(
        node=result, name=name, owner=owner, local_id=local_id,
        date_code=date_code, parasolid_version=parasolid_version,
        updated_at=updated_at, description=description,
    )
    fields["f0c"] &= 0xFFFD7FF8
    fields.update({
        "fc48": _initial_configuration_options(),
        "fc50": _initial_configuration_options(),
        "fca0": None,
        "fca8": None,
        "fce8": [{"o": _initial_component_configuration()}],
        "fba8": None,
        "fbb0": None,
        "fbc0": 0,
        "fbc4": 1,
        "fbc8": None,
        "fce0": None,
    })
    return result


def initial_assembly_model(*, name: str, allocator: PersistentIds, detail_definitions: dict, document_units: Obj) -> Obj:
    node = Obj("moAssembly_c")
    fields = model_fields(
        node=node, name=name, allocator=allocator, detail_definitions=detail_definitions,
        document_units=document_units, analysis_units=None,
        self_component=unit_component(owner=node), relation_graph=relation_manager(owner=node),
    )
    fields.update({name: {"n": 0, "items": []} for name in ("f14a0", "f14d8", "f18c8", "f18e8")})
    fields.update({name: None for name in ("f15a0", "f1608", "f1748", "f1740", "f1590", "f1868")})
    fields.update({name: 0 for name in ("f1560", "f1570", "f1750", "f1598", "f1710", "f1940", "has_f1a18", "has_f1a20")})
    fields.update(f1a28=1, f1674=-1)
    clear_model_update(model=node)
    return node


def ordinary_part_reference_stamps(*, child_model: Obj, child_header: Obj, assigned_transform: bool) -> dict:
    if not isinstance(child_model, Obj) or child_model.cls != "moPart_c":
        raise ValueError("ordinary part reference updates require a part model owner")
    if not isinstance(child_header, Obj) or child_header.cls != "moHeader_c":
        raise ValueError("ordinary part reference updates require a child header owner")
    if type(assigned_transform) is not bool:
        raise ValueError("placement assignment requires an explicit boolean")
    values = {"f3e0": child_header.f.get("f40"), "f3e8": child_header.f.get("f48"), "f3f4": child_model.f.get("f1300")}
    if any(type(value) is not int or not 0 <= value <= 0xFFFFFFFF for value in values.values()):
        raise ValueError("child reference update fields must fit the native unsigned domain")
    values.update(f3f0=101 + int(assigned_transform), f3f8=101)
    return values


def initial_mate_group(*, owner: Obj, name: str, allocator: PersistentIds, date_code: int, parasolid_version: int) -> Obj:
    if not isinstance(owner, Obj) or owner.cls != "moAssembly_c":
        raise ValueError("initial mate groups require an ordinary assembly owner")
    group = model_feature(cls="moMateGroup_c", name=name, owner=owner, allocator=allocator, date_code=date_code, parasolid_version=parasolid_version)
    group.f.update(discarded_manager_records=[], f4e8=[], f4f8=0)
    return group


def initial_assembly_features(*, owner: Obj, allocator: PersistentIds, folder_names: dict, plane_names: dict, cabinet_name: str, origin_name: str, mate_group_name: str, created_at: int, date_code: int, parasolid_version: int):
    early_folders = ("moCommentsFolder_c", "moFavoriteFolder_c", "moHistoryFolder_c", "moSelectionSetFolder_c", "moSensorFolder_c", "moLiveSectionFolder_c", "moDocsFolder_c")
    late_folders = ("moEnvFolder_c", "moInkMarkupFolder_c", "moEqnFolder_c")
    if not isinstance(owner, Obj) or owner.cls != "moAssembly_c" or set(folder_names) != set(early_folders + late_folders):
        raise ValueError("ordinary assembly feature construction requires exactly its classified system folders")
    args = {"owner": owner, "allocator": allocator, "date_code": date_code, "parasolid_version": parasolid_version}
    folders = {kind: folder(cls=kind, name=folder_names[kind], created_at=created_at, **args) for kind in early_folders + late_folders}
    owner["f1e0"] = folders["moEnvFolder_c"]
    cabinet = detail_cabinet(name=cabinet_name, **args)
    planes = principal_planes(names=plane_names, retain_construction_flag=True, **args)
    front = planes["z"]
    reference = component_plane(plane=front, component=owner["f990"], created_at=logged_creation_time(timestamps=()), principal_normal=(0.0, 0.0, 1.0))
    frame = PlaneFrame(origin=(0.0, 0.0, 0.0), u=front["_plane_u"], v=front["_plane_v"])
    origin = model_feature(cls="moOriginProfileFeature_c", name=origin_name, **args)
    origin_profile(profile=origin, plane=reference, frame=frame)
    group = initial_mate_group(name=mate_group_name, **args)
    return (*(folders[kind] for kind in early_folders), cabinet, *(folders[kind] for kind in late_folders), *planes.values(), origin, group)


def store_assembly_mates(*, registry, resolved_map, mate_group: Obj, mates: Sequence[Obj] = ()) -> bytes:
    if not isinstance(mate_group, Obj) or mate_group.cls != "moMateGroup_c":
        raise ValueError("mate-list serialization requires its actual mate group")
    group_items = mate_group["f60"]["list"]["items"]
    if group_items or mate_group["f4e8"] or mate_group["discarded_manager_records"]:
        raise ValueError("the resolved group must leave the separately serialized mate list empty")
    if any(mate.cls not in PLANAR_MATE_CLASSES.values() or mate.get("owner") is not mate_group for mate in mates):
        raise ValueError("the mate list requires supported planar mates registered with its actual group")
    return store_mate_list(mates, registry, FILE_VERSION, resolved_map=resolved_map)
