from __future__ import annotations

from collections.abc import Iterable
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
        self._allocated: dict[Obj, int] = {}

    @property
    def next_id(self) -> int:
        return self._next_id

    def allocate(self, node: Obj) -> int:
        if not isinstance(node, Obj):
            raise TypeError("persistent ids belong to archive objects")
        if node in self._allocated:
            value = self._allocated[node]
            if node.f.get("f08") != value:
                raise ArchiveError("allocated node id was changed outside its allocator")
            return value
        existing = node.f.get("f08", -1)
        if existing != -1:
            raise ArchiveError("fresh nodes cannot supply an existing persistent id")
        value = self._next_id
        while value in self._reserved:
            value += 1
        if value >= 0x7FFFFFFF:
            raise ArchiveError("persistent id space exhausted")
        self._next_id = value + 1
        self._allocated[node] = value
        node.f["f08"] = value
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
    if not isinstance(owner, Obj) or owner.cls != "moPart_c":
        raise ArchiveError("fresh unit components currently require a part owner")
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
    return Obj("moCompRef_c", component_reference_fields(component=component))


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
        "f9a8": 0x7FD,
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


@dataclass(slots=True)
class ModelGraph:
    part: Obj
    allocator: PersistentIds
    configuration_manager: Obj | None = None
    system_features: tuple[Obj, ...] = ()
    planes: dict[str, Obj] = field(default_factory=dict)

    @property
    def next_persistent_id(self) -> int:
        return self.allocator.next_id
