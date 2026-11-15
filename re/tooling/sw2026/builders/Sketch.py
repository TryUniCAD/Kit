from __future__ import annotations

from collections.abc import Iterator, MutableMapping, Sequence
from dataclasses import dataclass
from math import isclose, isfinite, sqrt

from Core import ArchiveError, Obj


class ConstructionError(ArchiveError):
    pass


class DerivedFields(MutableMapping):
    def __init__(self, *, fields=None, derived=None):
        self.fields = {} if fields is None else dict(fields)
        self.derived = {} if derived is None else dict(derived)
        if self.fields.keys() & self.derived.keys():
            raise ConstructionError("a field cannot be both authored and derived")

    def __getitem__(self, key):
        if key in self.derived:
            return self.derived[key]()
        return self.fields[key]

    def __setitem__(self, key, value):
        if key in self.derived:
            raise ConstructionError(f"cannot replace derived field {key}")
        self.fields[key] = value

    def __delitem__(self, key):
        if key in self.derived:
            raise ConstructionError(f"cannot remove derived field {key}")
        del self.fields[key]

    def __iter__(self) -> Iterator[str]:
        yield from self.fields
        yield from self.derived

    def __len__(self):
        return len(self.fields) + len(self.derived)


def _vector(*, value, size):
    result = tuple(float(component) for component in value)
    if len(result) != size or not all(isfinite(component) for component in result):
        raise ConstructionError(f"expected {size} finite coordinates")
    return result


def _dot(*, left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def _cross(*, left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _unit(*, value):
    vector = _vector(value=value, size=3)
    length = sqrt(_dot(left=vector, right=vector))
    if length == 0 or not isfinite(length):
        raise ConstructionError("frame axes must have finite nonzero length")
    return tuple(component / length for component in vector)


@dataclass(frozen=True, kw_only=True)
class PlaneFrame:
    origin: tuple[float, float, float]
    u: tuple[float, float, float]
    v: tuple[float, float, float]

    def __post_init__(self):
        origin = _vector(value=self.origin, size=3)
        u = _unit(value=self.u)
        v = _unit(value=self.v)
        if not isclose(_dot(left=u, right=v), 0.0, abs_tol=1e-12):
            raise ConstructionError("frame axes must be perpendicular")
        normal = _unit(value=_cross(left=u, right=v))
        v = _cross(left=normal, right=u)
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "u", u)
        object.__setattr__(self, "v", v)

    @property
    def normal(self):
        return _cross(left=self.u, right=self.v)

    def world_point(self, *, point):
        x, y = _vector(value=point, size=2)
        return tuple(o + x * u + y * v for o, u, v in zip(self.origin, self.u, self.v, strict=True))


def frame_transform(*, frame: PlaneFrame):
    rows = (*frame.u, *frame.v, *frame.normal)
    identity = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    fields = {
        "has_matrix": int(rows != identity),
        "t0": frame.origin[0],
        "t1": frame.origin[1],
        "t2": frame.origin[2],
        "scale": 1.0,
        "flags": 0,
    }
    if fields["has_matrix"]:
        fields["matrix"] = {f"m{i}": component for i, component in enumerate(rows)}
    return fields


def entity_visibility():
    return {
        "f00": 0xFFFF,
        "f02": 0x1F,
        "f04": 3,
        "f08": {"f00": 0xFFFFFFFF, "f04": 0xFFFF, "f08": {"f06": -1, "f00": -1.0}},
    }


def entity_fields(*, sketch: Obj):
    if sketch.cls != "sgSketch":
        raise ConstructionError("entity owner must be sgSketch")
    profile = sketch.get("f138")
    if not isinstance(profile, Obj) or profile.cls != "moProfileFeature_c" or sketch.get("f568") not in (-1, 0):
        raise ConstructionError("entity constructors require an ordinary 2D moProfileFeature_c owner")
    return {
        "_sketch": sketch,
        "f08": 0,
        "f0c": -1,
        "vis": entity_visibility(),
        "f20": 0,
        "dflt": 0,
        "f30": 5,
        "f34": 1,
        "f38": 1,
        "lw": {"f06": 0, "f00": -1.0},
        "ext": None,
        "f54": 4,
        "f56": 0,
        "f50": 0,
        "group": None,
        "has_name": 0,
        "f68": 1.0,
        "f74": 0,
        "f78": 0,
    }


def ordinary_point(*, sketch: Obj, position: Sequence[float]):
    x, y = _vector(value=position, size=2)
    fields = entity_fields(sketch=sketch)
    fields.update({
        "pflags": 0x1E,
        "pos": {"x": x, "y": y},
        "fe4": 0,
        "fe8": 0,
        "h1": None,
        "h2": None,
        "fec": 0,
        "f108": -2,
        "p1": {"x": 0.0, "y": 0.0},
        "p2": {"x": 0.0, "y": 0.0},
        "has_jet": 0,
        "ff0": 0,
    })
    return Obj("sgPoint", fields)


def _node_index(*, nodes: Sequence[Obj], node: Obj):
    for index, candidate in enumerate(nodes):
        if candidate is node:
            return index
    raise ConstructionError(f"{node.cls} is not in its owning geometry array")


def line_handle(*, sketch: Obj, line: Obj, lines: Sequence[Obj]):
    if sketch.cls != "sgSketch" or line.cls != "sgLine":
        raise ConstructionError("line handles require sgSketch and sgLine nodes")
    return Obj("sgLineHandle", DerivedFields(
        fields={"_sketch": sketch, "_line": line, "f1c": -1, "f08": 0},
        derived={
            "idx": lambda: min(_node_index(nodes=lines, node=line), 0x777F),
            "f18": lambda: _node_index(nodes=lines, node=line),
        },
    ))


def ordinary_line(*, sketch: Obj, start: Obj, end: Obj, points: Sequence[Obj]):
    if start is end or start.cls != "sgPoint" or end.cls != "sgPoint":
        raise ConstructionError("ordinary lines need two distinct sgPoint nodes")
    if start.get("_sketch") is not sketch or end.get("_sketch") is not sketch:
        raise ConstructionError("line endpoints must belong to the same sketch")
    fields = entity_fields(sketch=sketch)
    fields.update({"_start": start, "_end": end, "fd0": 0, "fd4": 0, "seg_tol": -1.0, "fe8": 0})
    return Obj("sgLine", DerivedFields(
        fields=fields,
        derived={
            "fc8_s": lambda: min(_node_index(nodes=points, node=start), 0xFFFF),
            "fc8": lambda: _node_index(nodes=points, node=start),
            "fcc_s": lambda: min(_node_index(nodes=points, node=end), 0xFFFF),
            "fcc": lambda: _node_index(nodes=points, node=end),
        },
    ))


def counted_fields(*, collections, fields=None):
    authored = {} if fields is None else dict(fields)
    derived = {}
    for count_name, item_name in collections.items():
        if item_name in authored or count_name in authored:
            raise ConstructionError(f"collection field overlaps {item_name}")
        items = []
        authored[item_name] = items
        derived[count_name] = lambda values=items: len(values)
    return DerivedFields(fields=authored, derived=derived)


def empty_object_list():
    return counted_fields(collections={"n": "items"})


def new_sketch(*, profile: Obj):
    if profile.cls != "moProfileFeature_c":
        raise ConstructionError("fresh 2D sketches require moProfileFeature_c")
    creation = {f"f{offset:02x}": 1 for offset in range(0x08, 0x40, 4)}
    creation["f40"] = 0
    dims = counted_fields(collections={
        "ng1": "val_g1", "ng2": "val_g2", "ng3": "val_g3", "noffset": "offset_dims",
        "nlog1": "log_g1", "nlog2": "log_g2", "nlog3": "log_g3", "niso": "iso",
        "nlinpatt": "linear_patterns", "nlincon": "linear_patt_cons", "ncircpatt": "circular_patterns",
        "ncirccon": "circular_patt_cons", "n7c0": "list_7c0", "n9f0": "list_9f0", "ngroup": "groups",
    }, fields={"f118": Obj("suObList", empty_object_list())})
    fields = counted_fields(collections={
        "npoints": "points", "nlines": "lines", "ntexts": "texts", "nhatches": "hatches",
        "narcs": "arcs", "nellipses": "ellipses", "nparabolas": "parabolas", "nsplines": "splines",
        "nplanes": "planes", "ncylinders": "cylinders", "nspheres": "spheres", "ncones": "cones",
        "nparametric": "parametric", "noffsets": "offsets", "nskoffsets": "sketch_offsets",
        "nstyled": "styled", "nintersections": "intersections", "ntools": "tools", "nblocks": "blocks",
        "nsilhouettes": "silhouettes",
    }, fields={
        "dims": dims,
        "f12c": 1,
        "f128": 1,
        "f130": 1,
        "f140": creation,
        "f37c": 0,
        "f188": 0xFFFF,
        "f18c": 0,
        "f190": 0,
        "f448": {"f08": "", "lw": {"f06": -1, "f00": -1.0}, "f10": -1, "f14": 1},
        "f568": -1,
        "f570": {"x": 0.0, "y": 0.0, "z": 0.0},
        "f56c": 1,
        "f578": 0,
        "f590": {"f78": empty_object_list(), "f40": counted_fields(collections={"n": "vars"})},
        "coinc": counted_fields(collections={f"m{i}_n": f"m{i}" for i in range(4)}),
        "f5d8": Obj("suObList", empty_object_list()),
        "f580": counted_fields(collections={"n": "blocks", "m": "map"}, fields={"f40": empty_object_list()}),
        "f598": counted_fields(collections={"n": "loops"}),
        "f588": counted_fields(collections={"n": "slots"}, fields={"f10": 0}),
        "f134": 0,
        "f138": profile,
    })
    return Obj("sgSketch", fields)


@dataclass(frozen=True, kw_only=True)
class ProfileGraph:
    profile: Obj
    sketch: Obj

    @property
    def point_count(self):
        return self.sketch["npoints"]

    @property
    def line_count(self):
        return self.sketch["nlines"]


def new_profile(*, profile: Obj, plane: Obj, frame: PlaneFrame):
    if profile.cls != "moProfileFeature_c" or type(profile.get("f08")) is not int or profile["f08"] < 0:
        raise ConstructionError("profile must be an allocated moProfileFeature_c from the model factory")
    if plane.cls != "moCompRefPlane_c":
        raise ConstructionError("profile plane must be a moCompRefPlane_c reference node")
    if "pd_f80" in profile.f:
        raise ConstructionError("profile already owns a sketch")
    transform = frame_transform(frame=frame)
    sketch = new_sketch(profile=profile)
    fields = {
        "f390": 0,
        "orig_dim_feature": None,
        "f3dc": 0,
        "pd_f80": sketch,
        "d5c0": counted_fields(collections={"n2a8": "f2a8"}, fields={"f2b0": 0}),
        "ca30": counted_fields(collections={"n238": "f238"}, fields={
            "f10": 3,
            "f198": {"empty": 1},
            "f168": empty_object_list(),
            "f188": {"elem": 0},
        }),
        "f3e0": 100000,
        "f3e8": empty_object_list(),
        "f3b8": None,
        "write_ref": 1,
        "pd_f78": plane,
        "pd_ff0": transform,
        "pd_has_fe8": 0,
        "pd_f100": 4,
        "pd_f110": None,
        "pd_f11c": -1,
        "pd_f118": 0,
        "pd_f2a0": 101,
        "f3c0": 0,
        "f388": None,
        "pd_f128": empty_object_list(),
        "pd_f148": empty_object_list(),
        "f42c": 0,
        "_frame": frame,
    }
    profile.f.update(fields)
    return ProfileGraph(profile=profile, sketch=sketch)
