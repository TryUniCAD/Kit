from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from Core import ArchiveError, Obj


class PersistentIds:
    def __init__(self, *, next_id: int = 0, reserved: Iterable[int] = ()):
        if type(next_id) is not int or not 0 <= next_id < 0x7FFFFFFF:
            raise ValueError("next persistent id must be a nonnegative signed integer")
        self._reserved = frozenset(reserved)
        if any(type(value) is not int or not 0 <= value < 0x7FFFFFFF for value in self._reserved):
            raise ValueError("reserved persistent ids must be nonnegative signed integers")
        self._next_id = next_id
        self._allocated: dict[tuple[Obj, str], int] = {}

    @property
    def next_id(self) -> int:
        return self._next_id

    def allocate(self, node: Obj, *, field: str = "f08") -> int:
        if not isinstance(node, Obj):
            raise TypeError("persistent ids belong to archive objects")
        if field not in ("f08", "f50"):
            raise ArchiveError("persistent id field is not classified for fresh construction")
        key = (node, field)
        if key in self._allocated:
            value = self._allocated[key]
            if node.f.get(field) != value:
                raise ArchiveError("allocated persistent id was changed outside its allocator")
            return value
        existing = node.f.get(field, -1)
        if existing != -1:
            raise ArchiveError("fresh nodes cannot supply an existing persistent id")
        value = self._next_id
        while value in self._reserved:
            value += 1
        if value >= 0x7FFFFFFF:
            raise ArchiveError("persistent id space exhausted")
        self._next_id = value + 1
        self._allocated[key] = value
        node.f[field] = value
        return value


def object_list(items: Iterable[Obj] = ()) -> dict:
    values = tuple(items)
    if any(not isinstance(value, Obj) for value in values):
        raise TypeError("object lists require archive objects")
    return {"n": len(values), "items": [{"o": value} for value in values]}


def node_list(items: Iterable[Obj] = ()) -> dict:
    return {"list": object_list(items), "tail": 0}


def entity_visibility() -> dict:
    return {
        "f00": 0xFFFF,
        "f02": 0,
        "f04": 3,
        "f08": {
            "f00": 0xFFFFFFFF,
            "f04": 0xFFFF,
            "f08": {"f06": -1, "f00": -1.0},
        },
    }


def node_fields(*, name: str, allocator: PersistentIds | None, node: Obj) -> dict:
    if not isinstance(name, str) or not name or "\x00" in name:
        raise ValueError("node names must be nonempty strings without null characters")
    fields = {
        "f18": Obj("moNodeName_c", {"f08": name}),
        "f0c": 1,
        "f28": 0x40000000,
        "f08": -1,
        "f2c": 0,
        "f20": "",
    }
    node.f.update(fields)
    if allocator is not None:
        allocator.allocate(node)
    return node.f


def concept_fields(*, name: str, allocator: PersistentIds | None, node: Obj) -> dict:
    fields = node_fields(name=name, allocator=allocator, node=node)
    fields.update({"has_list68": 0, "f78": None, "f60": node_list()})
    return fields


def feature(
    *,
    cls: str,
    name: str,
    owner: Obj,
    allocator: PersistentIds | None,
    date_code: int,
    parasolid_version: int,
    file_version: int = 19000,
    service_pack: int = 5,
    subservice_pack: int = 2,
    hidden: bool = False,
) -> Obj:
    if not isinstance(owner, Obj):
        raise TypeError("features require an archive-object owner")
    if not isinstance(cls, str) or not cls:
        raise ValueError("features require a runtime class name")
    if file_version != 19000:
        raise ArchiveError("fresh feature construction is classified only for archive version 19000")
    if any(type(value) is not int or not 0 <= value <= 255 for value in (service_pack, subservice_pack)):
        raise ValueError("service-pack fields must fit an unsigned byte")
    if type(date_code) is not int or not 0 <= date_code <= 0x7FFFFFFF:
        raise ValueError("date code must fit a nonnegative signed integer")
    if type(parasolid_version) is not int or not 0 < parasolid_version <= 0x7FFFFFFF:
        raise ValueError("Parasolid version must be an explicit positive integer")
    if type(hidden) is not bool:
        raise TypeError("feature visibility must be boolean")
    result = Obj(cls)
    fields = concept_fields(name=name, allocator=allocator, node=result)
    fields.update({
        "owner": owner,
        "f298": 0,
        "f28c": 0,
        "f29c": 101,
        "has_f1e8": 0,
        "f2a8": 0,
        "f2b8": 0,
        "f2bc": 0,
        "f2b0": file_version,
        "f1e0": 0.0,
        "f2b4": date_code,
        "f258": None,
        "f1f8": "",
        "f1f4": 0,
        "f2c8": entity_visibility(),
        "f2ec": 0,
        "fa8": 0,
        "f2f0": None,
        "f208": 0,
        "f300": service_pack,
        "f301": subservice_pack,
        "f318": 0,
        "hidden": int(hidden),
        "f30c": -1,
        "f2a4": 0,
        "f2a0": 0,
        "f98": 2,
        "f2ac": parasolid_version,
        "f344": 1,
        "f34c": 0,
        "f200": "",
    })
    return result


def model_feature(**values) -> Obj:
    result = feature(**values)
    result.f["f35c"] = 0
    return result


def atom_feature(**values) -> Obj:
    result = model_feature(**values)
    result.f.update({name: 0 for name in (
        "has_f3a8", "has_f528", "has_f530", "n494", "f540", "has_f548",
        "f544", "has_f4a8", "has_f4b0", "f4b8", "has_f4c0", "has_f4c8",
        "f578", "has_f550", "has_f3d0", "f5d0", "n678", "n5d8", "n400",
        "f490", "n3e0", "has_f6a8", "n610", "n620", "f6bc",
    )})
    result.f.update({name: [] for name in (
        "f498", "f678", "f5d8", "f400", "f3e0", "f610", "f620",
    )})
    result.f.update({
        "f368": object_list(),
        "f388": object_list(),
        "f538": None,
        "f4a0": 1,
    })
    return result


def body_feature(**values) -> Obj:
    result = atom_feature(**values)
    result.f.update({"f6e0": None, "f758": None, "f780": object_list(), "f7a0": 0})
    return result


def unit_component(*, owner: Obj) -> Obj:
    if not isinstance(owner, Obj) or owner.cls not in ("moPart_c", "moAssembly_c"):
        raise ArchiveError("fresh unit components require a classified part or assembly owner")
    return Obj("moUnitComponent_c", {"owner": owner, "has_ext": 0})


def component_reference_fields(*, component: Obj | None = None) -> dict:
    if component is not None and not isinstance(component, Obj):
        raise TypeError("component references require an archive-object component")
    return {
        "f58": component,
        "f68": 0,
        "f18": 0,
        "f1c": 0,
        "f20": 0,
        "f30": 0,
        "f70": 0,
        "f84": 0,
        "fa0": 0,
        "f34": 0,
        "f48": 0,
        "f90": -1,
        "f94": -1,
        "f98": -1,
        "f9c": -1,
        "has_fb0": 0,
        "has_fb8": 0,
        "has_fc0": 0,
        "has_fc8": 0,
        "has_fd0": 0,
        "f4c": 19000,
    }


def component_reference(*, component: Obj | None = None) -> Obj:
    raise ArchiveError("moCompRef_c is a nonserializable base; construct fields inside a concrete reference")


def logged_creation_time(*, timestamps: Iterable[int]) -> int:
    values = tuple(timestamps)
    if any(type(value) is not int or not 0 <= value <= 0xFFFFFFFF for value in values):
        raise ValueError("creation-log timestamps must fit native unsigned time32 fields")
    return values[0] if values else 2592000


def component_plane(
    *,
    plane: Obj,
    component: Obj,
    created_at: int,
    principal_normal: tuple[float, float, float] | None,
) -> Obj:
    if not isinstance(plane, Obj) or plane.cls != "moRefPlane_c":
        raise ArchiveError("plane wrappers require a native reference-plane node")
    if not isinstance(component, Obj) or component.cls != "moUnitComponent_c":
        raise ArchiveError("plane wrappers require a native unit-component node")
    identifier = plane.f.get("f08")
    if type(identifier) is not int or not 0 <= identifier < 0x7FFFFFFF:
        raise ArchiveError("plane wrappers require an allocated persistent plane id")
    if type(created_at) is not int or not 0 <= created_at <= 0xFFFFFFFF:
        raise ValueError("plane creation time must fit the archive timestamp field")
    axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    data = plane.f.get("f6f8")
    if not isinstance(data, Obj):
        raise ArchiveError("plane wrappers require the completed plane-data graph")
    if principal_normal is None:
        if data.cls == "moDefaultRefPlnData_c":
            raise ArchiveError("default planes require an explicit principal normal")
        kind = 0
    elif principal_normal in axes:
        normal = data.f.get("normal", {})
        if data.cls != "moDefaultRefPlnData_c" or tuple(normal.get(axis) for axis in ("x", "y", "z")) != principal_normal:
            raise ArchiveError("principal plane kind must agree with its native plane data")
        if plane.f.get("f34c") != 0:
            raise ArchiveError("principal plane kind requires the constructor discriminator state")
        kind = axes.index(principal_normal) + 1
    else:
        raise ArchiveError("principal plane normal must be a positive canonical axis")
    fields = component_reference_fields(component=component)
    fields.update({
        "ff0": {"f00": identifier, "f08": created_at},
        "ff8": None,
        "f100": kind,
    })
    return Obj("moCompRefPlane_c", fields)


def principal_plane(
    *,
    axis: str,
    name: str,
    owner: Obj,
    allocator: PersistentIds,
    date_code: int,
    parasolid_version: int,
    retain_construction_flag: bool,
) -> Obj:
    if axis not in ("x", "y", "z"):
        raise ValueError("principal planes require a positive canonical normal axis")
    if type(retain_construction_flag) is not bool:
        raise TypeError("reference-geometry construction flag selection must be boolean")
    axes = {label: tuple(float(i == index) for i in range(3)) for index, label in enumerate(("x", "y", "z"))}
    u = axes["x"] if axis != "x" else tuple(-value for value in axes["z"])
    v = axes["y"] if axis != "y" else tuple(-value for value in axes["z"])
    normal = (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )
    basis = (u, v, normal)
    transform = {
        "has_matrix": int(axis != "z"),
        "f58": 0.0,
        "f60": 0.0,
        "f68": 0.0,
        "f70": 1.0,
        "f78": 0,
    }
    if transform["has_matrix"]:
        transform["f08"] = {f"m{row * 3 + column}": basis[column][row] for row in range(3) for column in range(3)}
    data = Obj("moDefaultRefPlnData_c", {
        "root": dict.fromkeys(("x", "y", "z"), 0.0),
        "normal": dict(zip(("x", "y", "z"), normal, strict=True)),
        "f20": transform,
        "b0": 0.0,
        "b1": 0.0,
        "b2": 0.0,
        "b3": 0.0,
        "f48": None,
        "f50": 0,
        "f54": -4,
        "f58": -4,
        "old_e5": 0,
        "display_root": dict.fromkeys(("x", "y", "z"), 0.0),
        "f5c": 1,
        "f60": 0,
        "f64": 0,
        "f68": None,
        "f70": None,
        "f78": None,
    })
    result = atom_feature(
        cls="moRefPlane_c", name=name, owner=owner, allocator=allocator,
        date_code=date_code, parasolid_version=parasolid_version,
    )
    result.f.update({
        "f6c0": dict.fromkeys(("x", "y", "z"), 0.0),
        "f6dc": 1 | (4 if retain_construction_flag else 0),
        "f6e0": 0,
        "f6e8": None,
        "f6f0": 0,
        "f6f8": data,
        "_principal_axis": axis,
        "_plane_u": u,
        "_plane_v": v,
    })
    return result


def principal_planes(
    *,
    names: dict[str, str],
    owner: Obj,
    allocator: PersistentIds,
    date_code: int,
    parasolid_version: int,
    retain_construction_flag: bool,
) -> dict[str, Obj]:
    if set(names) != {"x", "y", "z"}:
        raise ValueError("principal plane names must identify each canonical normal axis")
    return {
        axis: principal_plane(
            axis=axis, name=names[axis], owner=owner, allocator=allocator,
            date_code=date_code, parasolid_version=parasolid_version,
            retain_construction_flag=retain_construction_flag,
        )
        for axis in ("z", "y", "x")
    }


def folder(
    *,
    cls: str,
    name: str,
    owner: Obj,
    allocator: PersistentIds,
    date_code: int,
    parasolid_version: int,
    created_at: int,
) -> Obj:
    supported = {
        "moCommentsFolder_c", "moDocsFolder_c", "moEnvFolder_c", "moEqnFolder_c",
        "moFavoriteFolder_c", "moHistoryFolder_c", "moMaterialFolder_c",
        "moNotesAreaFtrFolder_c", "moSelectionSetFolder_c", "moSensorFolder_c",
        "moSolidBodyFolder_c", "moSurfaceBodyFolder_c",
    }
    if cls not in supported:
        raise ArchiveError("system folder constructor is not classified for this runtime class")
    if not isinstance(owner, Obj):
        raise TypeError("system folders require an archive-object owner")
    if type(created_at) is not int or not 0 <= created_at <= 0xFFFFFFFF:
        raise ValueError("folder creation time must fit an unsigned Unix-seconds timestamp")
    if cls == "moEqnFolder_c" and (not isinstance(owner.f.get("f9d0"), Obj) or owner.f["f9d0"].cls != "moRelMgr_c"):
        raise ArchiveError("equation folders require the owner's native relation manager")
    result = feature(
        cls=cls, name=name, owner=owner, allocator=allocator, date_code=date_code,
        parasolid_version=parasolid_version,
    )
    ticks = (created_at + 11644473600) * 10_000_000
    low, high = ticks & 0xFFFFFFFF, ticks >> 32
    result.f.update({
        "f360": int(cls not in {"moCommentsFolder_c", "moSolidBodyFolder_c", "moSurfaceBodyFolder_c"}),
        "f370": 0,
        "f2a0": low - (1 << 32) if low & (1 << 31) else low,
        "f2a4": high - (1 << 32) if high & (1 << 31) else high,
    })
    if cls in {"moHistoryFolder_c", "moFavoriteFolder_c"}:
        result.f["f3c8"] = object_list()
    if cls == "moFavoriteFolder_c":
        result.f.update({"f3e8": object_list(), "f408": 1})
    if cls == "moSelectionSetFolder_c":
        result.f.update({"f3c0": object_list(), "f3e0": 1})
    if cls == "moMaterialFolder_c":
        result.f.update({"f378": "", "flags380": 0})
    if cls == "moNotesAreaFtrFolder_c":
        result.f.update({"f388": None, "f37c": 0, "f394": 0, "f378": 1, "f39c": 1})
    if cls in {"moSolidBodyFolder_c", "moSurfaceBodyFolder_c"}:
        result.f.update({"f37c": 0, "f380": 0, "f388": None, "f3d8": None})
    if cls == "moEqnFolder_c":
        result.f["_relation_manager"] = owner.f["f9d0"]
        owner.f["f9d0"].f["_equation_folder"] = result
    return result


def detail_cabinet(
    *,
    name: str,
    owner: Obj,
    allocator: PersistentIds,
    date_code: int,
    parasolid_version: int,
) -> Obj:
    result = model_feature(
        cls="moDetailCabinet_c", name=name, owner=owner, allocator=allocator,
        date_code=date_code, parasolid_version=parasolid_version,
    )
    result.f.update({
        "f368": object_list(),
        "f370": 1.0,
        "f378": 1.0,
        "f388": object_list(),
        "n3d8": 0,
        "f3d8": [],
        "f3f0": 0,
    })
    return result


def system_folders(
    *,
    names: dict[str, str],
    owner: Obj,
    allocator: PersistentIds,
    date_code: int,
    parasolid_version: int,
    created_at: int,
) -> tuple[Obj, ...]:
    if not isinstance(names, dict):
        raise TypeError("system folders require authored runtime-class/name pairs")
    return tuple(
        folder(
            cls=cls, name=name, owner=owner, allocator=allocator,
            date_code=date_code, parasolid_version=parasolid_version,
            created_at=created_at,
        )
        for cls, name in names.items()
    )


def empty_mass_properties() -> dict:
    result = {
        name: 0.0
        for name in (
            "f20", "f28", "f30", "f10", "f08", "f18", "f38", "f40", "f48",
            "f50", "f60", "f58", "f00", "fc8", "fd0", "fd8",
        )
    }
    result.update({
        "f1c0": 1,
        "f1c4": 0,
        "f1c8": 0,
        "f1cc": 0,
        "f1e0": 0,
        "f134": 0,
        "f138": 0,
        "f13c": 0,
        "f140": 0,
        "f148": "",
        "f150": "",
        "f1f0": 0,
        "f68": {"x": 1.0, "y": 0.0, "z": 0.0},
        "f80": {"x": 0.0, "y": 1.0, "z": 0.0},
        "f98": {"x": 0.0, "y": 0.0, "z": 1.0},
        "f15c": 1,
        "f128": 0,
    })
    return result


def part_config_object() -> dict:
    result = {name: None for name in ("fb0", "fb8", "fa0", "f88", "fa8")}
    result.update({
        name: object_list()
        for name in ("f10", "f60", "f100", "f80", "f68", "f58", "f78", "f70")
    })
    result.update({name: 0 for name in ("has_c8", "has_d0", "has_e0", "has_e8", "has_f0", "has_98", "fd8", "ff8")})
    result.update({"f0c": 1, "f08": -1})
    return result


def configuration(
    *,
    name: str,
    owner: Obj,
    local_id: int,
    date_code: int,
    parasolid_version: int,
    updated_at: int,
    description: str = "",
) -> Obj:
    if not isinstance(owner, Obj) or owner.cls != "moPart_c":
        raise ArchiveError("fresh part configurations require their actual part owner")
    if type(local_id) is not int or not 0 <= local_id < 0x7FFFFFFF:
        raise ValueError("configuration ids must be nonnegative signed integers")
    if type(updated_at) is not int or not 0 <= updated_at <= 0xFFFFFFFF:
        raise ValueError("configuration time must fit the archive timestamp field")
    if not isinstance(description, str) or "\x00" in description:
        raise ValueError("configuration descriptions must be strings without null characters")
    result = feature(
        cls="moPartConfiguration_c", name=name, owner=owner, allocator=None,
        date_code=date_code, parasolid_version=parasolid_version,
    )
    result.f["f08"] = local_id
    result.f.update({
        name: 0
        for name in (
            "f85c", "f670", "f6f8", "f688", "f968", "has610", "f784",
            "f828", "f82c", "f830", "f834", "f838", "f83c", "f840",
            "f850", "fb08", "fb34", "f74c", "hasb88", "fbd0", "f4c8",
            "f4cc", "fa80", "fc60", "fcc8", "fc64", "ndc8_hi", "ndc8_lo",
        )
    })
    result.f.update({name: [] for name in (
        "f618", "f358", "f380", "f3d0", "f420", "f430", "fb00", "f460",
        "fb10", "fa50", "fb58", "fa70", "f450", "fb70", "fb98", "fbf8",
        "fca8", "fce8", "fd20", "fdc8",
    )})
    result.f.update({
        f"n{name[1:]}": len(result.f[name])
        for name in (
            "f618", "f358", "f380", "f3d0", "f420", "f430", "fb00", "f460",
            "fb10", "fa50", "fb58", "fa70", "f450", "fb70", "fb98", "fbf8",
            "fca8", "fce8", "fd20",
        )
    })
    result.f.update({
        "f4a8": description,
        "f4b0": -1,
        "f4c4": 0x100,
        "f498": "",
        "f860": 101,
        "f668": empty_mass_properties(),
        "f678": updated_at,
        "f6a0": None,
        "f6a8": object_list(),
        "f528": object_list(),
        "f9a8": result.f["f2b0"],
        "f96c": 1,
        "f660": None,
        "fa98": object_list(),
        "faf0": 0,
        "faf4": 1,
        "f788": 1,
        "f78c": -1.0,
        "f790": -1.0,
        "fb30": 1,
        "f844": 1,
        "f750": -1,
        "fbd4": 1,
        "f600": {"n": 0, "items": []},
        "fb68": {"n": 0, "items": []},
        "fb80": None,
        "fbd8": None,
        "f4d0": part_config_object(),
        "fc50": -1.0,
        "fc48": None,
        "fcb8": None,
        "fcc0": None,
        "fccc": -1,
        "fcd4": -1,
        "fcd0": -1,
    })
    return result


def configuration_manager(
    *,
    owner: Obj,
    names: Iterable[str],
    date_code: int,
    parasolid_version: int,
    updated_at: int,
    current: int = 0,
) -> Obj:
    names = tuple(names)
    if not names or len(set(names)) != len(names):
        raise ValueError("a configuration manager requires distinct configuration names")
    if type(current) is not int or not 0 <= current < len(names):
        raise ValueError("current configuration must select an authored configuration")
    result = feature(
        cls="moConfigurationMgr_c", name="Configurations", owner=owner,
        allocator=None, date_code=date_code, parasolid_version=parasolid_version,
    )
    configs = tuple(
        configuration(
            name=name, owner=owner, local_id=index, date_code=date_code,
            parasolid_version=parasolid_version, updated_at=updated_at,
        )
        for index, name in enumerate(names)
    )
    result.f.update({
        "f360": configs[current],
        "f368": configs[current],
        "f0c": result.f["f0c"] & 0xFFFD7FF8,
        "f40c": len(configs),
        "f370": object_list(configs),
        "f55c": 0,
        "f578": "",
        "f5b0": Obj("suObList", object_list()),
        "f658": 0,
        "f6d0": None,
        "f730": {"n": 0, "items": []},
        "f758": 0,
        "f75c": 2,
        "f810": "",
        "f818": 0,
        "f81c": 0,
        "f830": 0xFFFFFFFF,
        "f860": 0,
        "has8a0": 0,
    })
    for count, items in (
        ("n_ext", "ext"), ("n590", "f590"), ("n5b8", "f5b8"),
        ("n600", "f600"), ("n5d0", "f5d0"), ("n660", "f660"),
        ("n6b0", "f6b0"), ("n6e0a", "f6e0a"), ("n6e0b", "f6e0b"),
        ("n6e8a", "f6e8a"), ("n6e8b", "f6e8b"), ("n708", "f708"),
        ("n7f8", "f7f8"), ("n820", "f820"), ("n6c0", "f6c0"),
    ):
        result.f[count] = 0
        result.f[items] = []
    return result


def relation_manager(*, owner: Obj) -> Obj:
    if not isinstance(owner, Obj) or owner.cls not in ("moPart_c", "moAssembly_c"):
        raise ArchiveError("fresh relation managers require a classified part or assembly owner")
    return Obj("moRelMgr_c", {
        "owner": owner,
        "f58": object_list(),
        "f10": {"n": 0, "items": []},
        "f170": "",
        "f178": 0,
        "f180": 0,
        "f150": 0,
        "ff4": -1,
        "fa0": object_list(),
        "f1b0": -1,
        "n1c0": 0,
        "f1c0": [],
    })


def clear_model_update(*, model: Obj) -> None:
    if not isinstance(model, Obj) or model.cls not in ("moModel_c", "moPart_c"):
        raise ArchiveError("zero-status model update is classified only for model and part owners")
    flags = model.f.get("f0c")
    if type(flags) is not int or not 0 <= flags <= 0xFFFFFFFF:
        raise ArchiveError("model update requires an initialized unsigned flag word")
    model.f["f0c"] = flags & 0xFFFD7FF8


def mark_model_update(*, model: Obj) -> None:
    if not isinstance(model, Obj) or model.cls not in ("moModel_c", "moPart_c"):
        raise ArchiveError("positive model update is classified only for model and part owners")
    flags = model.f.get("f0c")
    if type(flags) is not int or not 0 <= flags <= 0xFFFFFFFF:
        raise ArchiveError("model update requires an initialized unsigned flag word")
    model.f["f0c"] = (flags & 0xFFFD7FF9) | 1


def _model_collections() -> dict:
    fields = {name: [] for name in (
        "f168", "f178", "fcd8", "f1310", "fec0", "f1288", "ffe0",
        "f10b0", "f1d0",
    )}
    fields.update({name: 0 for name in (
        "n168", "n180", "ncd8", "n1318", "nec8", "n1290", "nff4",
        "n10c4", "n1d8",
    )})
    fields.update({name: object_list() for name in (
        "fc90", "fb08", "f9c8", "fb30", "fba8", "fb58", "fb80",
        "fbf8", "fbd0", "fc20", "fc70", "f240",
    )})
    fields["fdd0"] = {"n08": 0, "faces": [], "n58": 0, "props": []}
    return fields


def _part_collections() -> dict:
    fields = {name: [] for name in (
        "f1108", "f1130", "f1628", "f16e8", "f1640",
    )}
    fields.update({name: 0 for name in ("n1118", "n1140", "n16f8")})
    fields.update({
        "f938": {"n08": 0, "bodies": [], "n58": 0, "props": []},
        "f1c70": {"n": 0, "items": []},
    })
    return fields


def model_fields(
    *,
    node: Obj,
    name: str,
    allocator: PersistentIds,
    detail_definitions: dict,
    document_units: Obj,
    analysis_units: Obj,
    self_component: Obj | None,
    relation_graph: Obj | None,
) -> dict:
    if not isinstance(node, Obj) or node.cls not in ("moPart_c", "moAssembly_c") or node.f:
        raise ArchiveError("base model fields require a fresh empty part or assembly record")
    if not isinstance(detail_definitions, dict) or not detail_definitions:
        raise ArchiveError("model construction requires generated detail definitions")
    if any(not isinstance(units, Obj) or units.cls != "moUnitsTable_c" for units in (document_units, analysis_units)):
        raise ArchiveError("model construction requires explicit native unit-table graphs")
    if self_component is not None:
        if not isinstance(self_component, Obj) or self_component.cls != "moUnitComponent_c":
            raise ArchiveError("fresh model self components must be native unit components")
        if self_component.f.get("owner") is not node:
            raise ArchiveError("the native self component must point to its actual model record")
    if relation_graph is not None and (not isinstance(relation_graph, Obj) or relation_graph.cls != "moRelMgr_c" or relation_graph.f.get("owner") is not node):
        raise ArchiveError("the relation graph must belong to its actual model record")
    fields = concept_fields(name=name, allocator=allocator, node=node)
    fields.update(_model_collections())
    fields.update({field_name: 0 for field_name in (
        "fb0", "fb4", "fd30", "has_f7f8", "fef8", "ff18", "ff20", "ff2c",
        "f160", "ff1c", "shrinkwrap", "defeatured", "fd58", "f1188", "f118c",
        "f1190", "f1194", "has_f1180", "f280", "f1308", "fd2c",
        "has_fdb8", "fd48", "ff3c", "f1010", "fb00", "fd54", "has_f1270",
    )})
    fields.update({field_name: None for field_name in (
        "fa70", "f2f8", "f1e0", "f9d8", "fa88", "attach", "fe80",
        "fa48", "fa90", "fed0", "fe38", "fa50", "f12d0", "f1338",
    )})
    fields.update({
        "f2c": fields["f2c"] | 0x100,
        "f9b8": document_units,
        "f9c0": analysis_units,
        "fae0": detail_definitions,
        "f990": self_component,
        "f9d0": relation_graph,
        "fdb0": Obj("moTransRefPlaneData_c", {"f08": 1, "f0c": 1, "f10": 0xFF00, "f14": 0xFF, "f18": 0x5F, "f1c": 0}),
        "ff80": 1000.0,
        "ff88": 1e-8,
        "fa98": {"kind": 2, "f18": {"n": 0, "items": []}, "f110": -0x55555556, "f114": -0x44444445},
        "fd50": 1,
        "f784": bytes(16),
        "f7a4": bytes(16),
        "f1300": 101,
        "fd88": {"f260": 100, "n6c": 0, "atoms": [], "fa8": 0},
        "fd90": {"f80": 10000, "fe0": 0, "n": 0, "objects": []},
        "f9f8": [{"o": None} for _ in range(10)],
        "fce8": 0x32,
        "fcec": 0x6C,
        "fd44": 10,
        "feb0": 199,
        "feb4": 199,
        "feb8": 0,
        "f760": "",
        "f768": "",
    })
    return fields


def part_root(
    *,
    name: str,
    allocator: PersistentIds,
    detail_definitions: dict,
    document_units: Obj,
    analysis_units: Obj,
    hatch_name: str,
) -> Obj:
    if not isinstance(hatch_name, str) or not hatch_name or "\x00" in hatch_name:
        raise ValueError("crosshatch names must be authored nonempty strings without null characters")
    result = Obj("moPart_c")
    fields = model_fields(
        node=result, name=name, allocator=allocator,
        detail_definitions=detail_definitions, document_units=document_units,
        analysis_units=analysis_units, self_component=unit_component(owner=result),
        relation_graph=relation_manager(owner=result),
    )
    fields.update(_part_collections())
    fields.update({field_name: 0 for field_name in (
        "f15f0", "f1614", "f1618", "f161c", "f1014", "f14f8", "f1428",
        "f14d8", "f152c", "f1400", "f1698", "f169c", "has_f16b8", "f1638",
        "f18d4", "f1900", "f1be0",
    )})
    fields.update({"f1420": None, "f13f8": None})
    fields.update({
        "f1418": Obj("gcXhatch_c", {"f08": hatch_name, "f10": 0.0, "f18": 1.0, "f34": 0, "f20": 0, "f24": 1, "f28": -1, "f2c": -1, "f30": 0}),
        "f1588": Obj("uoModelData_c", {"f08": None, "f10": 0}),
        "f1104": 20,
        "f1128": 20,
        "f18d8": 101,
    })
    return result


@dataclass(slots=True)
class ModelGraph:
    part: Obj
    allocator: PersistentIds
    configuration_manager: Obj | None = None
    system_features: tuple[Obj, ...] = ()
    planes: dict[str, Obj] = field(default_factory=dict)
    folders: dict[str, Obj] = field(default_factory=dict)
    cabinet: Obj | None = None

    @property
    def next_persistent_id(self) -> int:
        return self.allocator.next_id


def part_graph(
    *,
    name: str,
    configuration_names: Iterable[str],
    plane_names: dict[str, str],
    folder_names: Mapping[str, str],
    cabinet_name: str,
    detail_definitions: dict,
    document_units: Obj,
    analysis_units: Obj,
    hatch_name: str,
    date_code: int,
    parasolid_version: int,
    updated_at: int,
    created_at: int,
    retain_construction_flag: bool,
) -> ModelGraph:
    required_folders = {
        "moCommentsFolder_c", "moDocsFolder_c", "moEnvFolder_c", "moEqnFolder_c",
        "moFavoriteFolder_c", "moHistoryFolder_c", "moMaterialFolder_c",
        "moNotesAreaFtrFolder_c", "moSelectionSetFolder_c", "moSensorFolder_c",
        "moSolidBodyFolder_c", "moSurfaceBodyFolder_c",
    }
    if not isinstance(folder_names, Mapping) or set(folder_names) != required_folders:
        raise ArchiveError("base part graphs require authored names for every classified system folder")
    allocator = PersistentIds()
    part = part_root(
        name=name, allocator=allocator, detail_definitions=detail_definitions,
        document_units=document_units, analysis_units=analysis_units,
        hatch_name=hatch_name,
    )
    manager = configuration_manager(
        owner=part, names=configuration_names, date_code=date_code,
        parasolid_version=parasolid_version, updated_at=updated_at,
    )
    folders = {
        cls: folder(
            cls=cls, name=label, owner=part, allocator=allocator,
            date_code=date_code, parasolid_version=parasolid_version,
            created_at=created_at,
        )
        for cls, label in folder_names.items()
    }
    cabinet = detail_cabinet(
        name=cabinet_name, owner=part, allocator=allocator,
        date_code=date_code, parasolid_version=parasolid_version,
    )
    part.f["f1e0"] = folders["moEnvFolder_c"]
    part.f["_folder_caches"] = {
        "f1e0": folders["moEnvFolder_c"],
        "f1f0": folders["moDocsFolder_c"],
        "f1f8": folders["moCommentsFolder_c"],
        "f200": folders["moSensorFolder_c"],
        "f218": folders["moFavoriteFolder_c"],
        "f220": folders["moSelectionSetFolder_c"],
        "f228": folders["moHistoryFolder_c"],
        "f1500": folders["moSurfaceBodyFolder_c"],
        "f1508": folders["moSolidBodyFolder_c"],
    }
    planes = principal_planes(
        names=plane_names, owner=part, allocator=allocator, date_code=date_code,
        parasolid_version=parasolid_version,
        retain_construction_flag=retain_construction_flag,
    )
    system_features = (*folders.values(), cabinet, *planes.values())
    for node in system_features:
        node.f["f0c"] &= 0xFFFD7FF8
    return ModelGraph(
        part=part, allocator=allocator, configuration_manager=manager,
        system_features=system_features, planes=planes, folders=folders,
        cabinet=cabinet,
    )
