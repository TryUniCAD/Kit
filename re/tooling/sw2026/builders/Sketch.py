from __future__ import annotations

from collections.abc import Iterator, MutableMapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
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


class NodeOrder(Sequence):
    def __init__(self, *, nodes):
        self.nodes = tuple(nodes)
        if any(not isinstance(node, Obj) for node in self.nodes):
            raise ConstructionError("geometry arrays require Core.Obj nodes")
        if len({id(node) for node in self.nodes}) != len(self.nodes):
            raise ConstructionError("geometry arrays must not repeat a node identity")
        self.positions = None

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, key):
        return self.nodes[key]

    def index_of(self, *, node):
        if self.positions is None:
            self.positions = {id(value): index for index, value in enumerate(self.nodes)}
        try:
            return self.positions[id(node)]
        except KeyError as error:
            raise ConstructionError(f"{node.cls} is not in its owning geometry array") from error


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
        return _vector(value=(o + x * u + y * v for o, u, v in zip(self.origin, self.u, self.v, strict=True)), size=3)


def frame_transform(*, frame: PlaneFrame):
    rows = (*frame.u, *frame.v, *frame.normal)
    identity = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    fields = {
        "has_matrix": int(rows != identity),
        "f58": frame.origin[0],
        "f60": frame.origin[1],
        "f68": frame.origin[2],
        "f70": 1.0,
        "f78": 0,
    }
    if fields["has_matrix"]:
        fields["f08"] = {f"m{i}": component for i, component in enumerate(rows)}
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
    if not isinstance(profile, Obj) or profile.cls not in ("moProfileFeature_c", "moOriginProfileFeature_c") or sketch.get("f568") not in (-1, 0):
        raise ConstructionError("entity constructors require an ordinary 2D profile owner")
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


def point_handle(*, sketch: Obj, point: Obj, points: NodeOrder):
    if sketch.cls != "sgSketch" or point.cls != "sgPoint" or point.get("_sketch") is not sketch:
        raise ConstructionError("point handles require a point owned by their sketch")
    return Obj("sgPointHandle", DerivedFields(
        fields={"_sketch": sketch, "_point": point, "f1c": -1, "f08": 0},
        derived={
            "idx": lambda: min(_node_index(nodes=points, node=point), 0x777F),
            "f18": lambda: _node_index(nodes=points, node=point),
        },
    ))


def dimension_fields():
    return {
        "refcount": 0,
        "f28": None,
        "f48": None,
        "f50": -1,
        "f30": 0,
        "f54": 0,
        "f5c": 0,
        "f60": None,
        "f68": 0,
        "has_f78": 0,
    }


def _node_index(*, nodes: NodeOrder, node: Obj):
    if not isinstance(nodes, NodeOrder):
        raise ConstructionError("geometry references require a shared immutable NodeOrder")
    return nodes.index_of(node=node)


def line_handle(*, sketch: Obj, line: Obj, lines: NodeOrder):
    if sketch.cls != "sgSketch" or line.cls != "sgLine":
        raise ConstructionError("line handles require sgSketch and sgLine nodes")
    return Obj("sgLineHandle", DerivedFields(
        fields={"_sketch": sketch, "_line": line, "f1c": -1, "f08": 0},
        derived={
            "idx": lambda: min(_node_index(nodes=lines, node=line), 0x777F),
            "f18": lambda: _node_index(nodes=lines, node=line),
        },
    ))


def ordinary_line(*, sketch: Obj, start: Obj, end: Obj, points: NodeOrder):
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
    result = DerivedFields(fields=fields)
    for count_name, item_name in collections.items():
        if item_name in result or count_name in result:
            raise ConstructionError(f"collection field overlaps {item_name}")
        result[item_name] = []
        result.derived[count_name] = lambda name=item_name: len(result[name])
    return result


def empty_object_list():
    return counted_fields(collections={"n": "items"})


def new_sketch(*, profile: Obj):
    if profile.cls not in ("moProfileFeature_c", "moOriginProfileFeature_c"):
        raise ConstructionError("fresh 2D sketches require an ordinary or origin profile")
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

    @property
    def points(self):
        return tuple(self.sketch.get("_point_nodes", ()))

    @property
    def lines(self):
        return tuple(self.sketch.get("_line_nodes", ()))


def new_profile(*, profile: Obj, plane: Obj, frame: PlaneFrame):
    if profile.cls not in ("moProfileFeature_c", "moOriginProfileFeature_c") or type(profile.get("f08")) is not int or profile["f08"] < 0:
        raise ConstructionError("profile must be an allocated ordinary or origin profile from the model factory")
    if plane.cls != "moCompRefPlane_c":
        raise ConstructionError("profile plane must be a moCompRefPlane_c reference node")
    if not isinstance(frame, PlaneFrame):
        raise ConstructionError("profile placement requires a PlaneFrame")
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


def origin_profile(*, profile: Obj, plane: Obj, frame: PlaneFrame):
    if profile.cls != "moOriginProfileFeature_c":
        raise ConstructionError("origin construction requires an allocated moOriginProfileFeature_c")
    if frame.origin != (0.0, 0.0, 0.0):
        raise ConstructionError("a document origin profile requires the semantic model origin")
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    profile["pd_f11c"] &= ~6
    point = ordinary_point(sketch=graph.sketch, position=(0.0, 0.0))
    point["fe4"] = 1
    point["f0c"] = 1
    points = NodeOrder(nodes=(point,))
    handle = point_handle(sketch=graph.sketch, point=point, points=points)
    fields = dimension_fields()
    fields.update({"_sketch": graph.sketch, "f80": 0x11, "f90": 2, "f94": 0, "f98": 0, "fa0": 0xFFFE, "fa4": 0, "h1": handle})
    constraint = Obj("sgLogG1Dim", fields)
    point["_constraints"] = (constraint,)
    del point.f["f20"]
    point.f = DerivedFields(fields=point.f, derived={"f20": lambda: len(point["_constraints"])})
    graph.sketch["points"].append({"kind": 0, "point": point.f})
    graph.sketch["dims"]["log_g1"].append({"d": constraint.f})
    graph.sketch["f140"]["f08"] = 2
    graph.sketch["_point_nodes"] = points
    graph.sketch["_line_nodes"] = NodeOrder(nodes=())
    graph.sketch["_origin_constraint"] = constraint
    _bind_local_ref_flag(sketch=graph.sketch)
    graph.sketch["_requires_update"] = True
    return graph


def _local_ref_flag(*, sketch: Obj):
    if sketch["f138"].get("pd_f110") is not None:
        raise ConstructionError("derived-profile reference state requires additional native update rules")
    for name in ("points", "lines"):
        field = "point" if name == "points" else "line"
        if any(entry[field]["ext"] is not None for entry in sketch[name]):
            raise ConstructionError("external sketch geometry requires additional native update rules")
    for name in ("texts", "hatches", "arcs", "ellipses", "parabolas", "splines", "planes", "cylinders", "spheres", "cones", "parametric", "styled", "blocks", "silhouettes"):
        if sketch[name]:
            raise ConstructionError(f"reference-state inference is not established for {name}")
    dims = sketch["dims"]
    for name in ("val_g1", "val_g2", "val_g3", "offset_dims", "log_g2", "log_g3", "iso", "linear_patterns", "linear_patt_cons", "circular_patterns", "circular_patt_cons", "list_7c0", "list_9f0", "groups"):
        if dims[name]:
            raise ConstructionError(f"reference-state inference is not established for {name}")
    for record in dims["log_g1"]:
        handle = record["d"]["h1"]
        if record["d"]["f80"] != 0x11 or not isinstance(handle, Obj) or handle.cls != "sgPointHandle" or handle["f1c"] != -1:
            raise ConstructionError("logical-constraint reference state requires a constructed local origin constraint")
    return 0


def _bind_local_ref_flag(*, sketch: Obj):
    del sketch.f["f188"]
    sketch.f.derived["f188"] = lambda: _local_ref_flag(sketch=sketch)


def _orientation(*, a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(*, a, b, point):
    return min(a[0], b[0]) <= point[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= point[1] <= max(a[1], b[1])


def _intersects(*, a, b, c, d):
    signs = (
        _orientation(a=a, b=b, c=c),
        _orientation(a=a, b=b, c=d),
        _orientation(a=c, b=d, c=a),
        _orientation(a=c, b=d, c=b),
    )
    first, second, third, fourth = signs
    if ((first > 0 > second) or (second > 0 > first)) and ((third > 0 > fourth) or (fourth > 0 > third)):
        return True
    return (
        (first == 0 and _on_segment(a=a, b=b, point=c))
        or (second == 0 and _on_segment(a=a, b=b, point=d))
        or (third == 0 and _on_segment(a=c, b=d, point=a))
        or (fourth == 0 and _on_segment(a=c, b=d, point=b))
    )


@dataclass(frozen=True, kw_only=True)
class _SweepEdge:
    index: int
    start: tuple[Fraction, Fraction]
    end: tuple[Fraction, Fraction]
    slope: Fraction | None

    def y_at(self, *, x):
        if self.slope is None:
            raise ConstructionError("vertical edges require the sweep range branch")
        return self.start[1] + (x - self.start[0]) * self.slope


@dataclass(eq=False, kw_only=True)
class _SweepNode:
    edge: _SweepEdge
    parent: _SweepNode | None = None
    left: _SweepNode | None = None
    right: _SweepNode | None = None
    height: int = 1


class _SweepTree:
    def __init__(self):
        self.root = None
        self.nodes = {}
        self.x = Fraction(0)

    def _height(self, *, node):
        return 0 if node is None else node.height

    def _refresh(self, *, node):
        node.height = 1 + max(self._height(node=node.left), self._height(node=node.right))

    def _replace(self, *, node, replacement):
        if node.parent is None:
            self.root = replacement
        elif node.parent.left is node:
            node.parent.left = replacement
        else:
            node.parent.right = replacement
        if replacement is not None:
            replacement.parent = node.parent

    def _rotate(self, *, node, left):
        pivot = node.right if left else node.left
        if pivot is None:
            raise ConstructionError("invalid sweep-tree rotation")
        self._replace(node=node, replacement=pivot)
        middle = pivot.left if left else pivot.right
        if left:
            node.right = middle
            pivot.left = node
        else:
            node.left = middle
            pivot.right = node
        if middle is not None:
            middle.parent = node
        node.parent = pivot
        self._refresh(node=node)
        self._refresh(node=pivot)
        return pivot

    def _rebalance(self, *, node):
        while node is not None:
            self._refresh(node=node)
            balance = self._height(node=node.left) - self._height(node=node.right)
            if balance > 1:
                if self._height(node=node.left.left) < self._height(node=node.left.right):
                    self._rotate(node=node.left, left=True)
                node = self._rotate(node=node, left=False)
            elif balance < -1:
                if self._height(node=node.right.right) < self._height(node=node.right.left):
                    self._rotate(node=node.right, left=False)
                node = self._rotate(node=node, left=True)
            node = node.parent

    def _key(self, *, edge):
        return edge.y_at(x=self.x), edge.slope, edge.index

    def insert(self, *, edge):
        node = _SweepNode(edge=edge)
        if self.root is None:
            self.root = node
        else:
            parent = self.root
            key = self._key(edge=edge)
            while True:
                left = key < self._key(edge=parent.edge)
                child = parent.left if left else parent.right
                if child is None:
                    node.parent = parent
                    if left:
                        parent.left = node
                    else:
                        parent.right = node
                    break
                parent = child
            self._rebalance(node=parent)
        self.nodes[edge.index] = node
        return node

    def before(self, *, node):
        if node.left is not None:
            node = node.left
            while node.right is not None:
                node = node.right
            return node
        while node.parent is not None and node.parent.left is node:
            node = node.parent
        return node.parent

    def after(self, *, node):
        if node.right is not None:
            node = node.right
            while node.left is not None:
                node = node.left
            return node
        while node.parent is not None and node.parent.right is node:
            node = node.parent
        return node.parent

    def lower_y(self, *, y):
        node, found = self.root, None
        while node is not None:
            if node.edge.y_at(x=self.x) >= y:
                found = node
                node = node.left
            else:
                node = node.right
        return found

    def remove(self, *, index):
        node = self.nodes.pop(index)
        if node.left is not None and node.right is not None:
            following = self.after(node=node)
            node.edge, following.edge = following.edge, node.edge
            self.nodes[node.edge.index] = node
            node = following
        parent = node.parent
        self._replace(node=node, replacement=node.left if node.left is not None else node.right)
        self._rebalance(node=parent)


def _reject_crossing(*, first, second, count):
    if first is None or second is None or abs(first.index - second.index) in (1, count - 1):
        return
    if _intersects(a=first.start, b=first.end, c=second.start, d=second.end):
        raise ConstructionError("closed polygon edges must not intersect or touch away from shared endpoints")


def _sweep_ring(*, points):
    count = len(points)
    events = {}
    for i, point in enumerate(points):
        start, end = sorted((point, points[(i + 1) % count]))
        vertical = start[0] == end[0]
        edge = _SweepEdge(index=i, start=start, end=end, slope=None if vertical else (end[1] - start[1]) / (end[0] - start[0]))
        beginning = events.setdefault(start[0], {"starts": [], "ends": [], "verticals": []})
        if vertical:
            beginning["verticals"].append(edge)
        else:
            beginning["starts"].append(edge)
            events.setdefault(end[0], {"starts": [], "ends": [], "verticals": []})["ends"].append(edge)
    tree = _SweepTree()
    for x, event in sorted(events.items()):
        tree.x = x
        for edge in event["starts"]:
            node = tree.insert(edge=edge)
            before, after = tree.before(node=node), tree.after(node=node)
            _reject_crossing(first=edge, second=None if before is None else before.edge, count=count)
            _reject_crossing(first=edge, second=None if after is None else after.edge, count=count)
        previous = None
        for edge in sorted(event["verticals"], key=lambda item: item.start[1]):
            if previous is not None and edge.start[1] <= previous.end[1]:
                _reject_crossing(first=previous, second=edge, count=count)
            if previous is None or edge.end[1] > previous.end[1]:
                previous = edge
            node = tree.lower_y(y=edge.start[1])
            while node is not None and node.edge.y_at(x=x) <= edge.end[1]:
                _reject_crossing(first=edge, second=node.edge, count=count)
                node = tree.after(node=node)
        for edge in event["ends"]:
            node = tree.nodes[edge.index]
            before, after = tree.before(node=node), tree.after(node=node)
            _reject_crossing(first=None if before is None else before.edge, second=None if after is None else after.edge, count=count)
            tree.remove(index=edge.index)


def polygon_vertices(*, vertices):
    points = tuple(_vector(value=point, size=2) for point in vertices)
    count = len(points)
    if not 3 <= count < 0x7FFFFFFF:
        raise ConstructionError("closed polygons require at least three vertices within signed array limits")
    if len(set(points)) != count:
        raise ConstructionError("polygon vertices must be distinct, with closure represented by the final edge")
    exact = tuple(tuple(Fraction(value) for value in point) for point in points)
    area = sum(exact[i][0] * exact[(i + 1) % count][1] - exact[(i + 1) % count][0] * exact[i][1] for i in range(count))
    if area == 0:
        raise ConstructionError("polygon area must be nonzero")
    for i, point in enumerate(exact):
        before, after = exact[i - 1], exact[(i + 1) % count]
        if _orientation(a=before, b=point, c=after) == 0 and not _on_segment(a=before, b=after, point=point):
            raise ConstructionError("adjacent polygon edges must not overlap")
    _sweep_ring(points=exact)
    return points


def closed_profile(*, vertices, profile: Obj, plane: Obj, frame: PlaneFrame):
    if profile.cls != "moProfileFeature_c":
        raise ConstructionError("polygon construction requires an ordinary moProfileFeature_c")
    positions = polygon_vertices(vertices=vertices)
    if not isinstance(frame, PlaneFrame):
        raise ConstructionError("profile placement requires a PlaneFrame")
    for position in positions:
        frame.world_point(point=position)
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    sketch = graph.sketch
    points = NodeOrder(nodes=(ordinary_point(sketch=sketch, position=position) for position in positions))
    lines = NodeOrder(nodes=(ordinary_line(sketch=sketch, start=point, end=points[(i + 1) % len(points)], points=points) for i, point in enumerate(points)))
    for point in points:
        del point.f["f0c"]
        point.f = DerivedFields(fields=point.f, derived={"f0c": lambda node=point: _node_index(nodes=points, node=node) + 1})
    for line in lines:
        del line.f["f0c"]
        del line.f["f08"]
        line.f.derived["f0c"] = lambda node=line: _node_index(nodes=lines, node=node) + 1
        line.f.derived["f08"] = lambda node=line: _node_index(nodes=lines, node=node) + 1
        line["fd0"] = 1
    for i, point in enumerate(points):
        incident = (lines[0], lines[-1]) if i == 0 else (lines[i - 1], lines[i])
        point["h1"] = line_handle(sketch=sketch, line=incident[0], lines=lines)
        point["h2"] = line_handle(sketch=sketch, line=incident[1], lines=lines)
        point.f.derived["fe8"] = lambda edges=incident: len(edges)
        del point.f.fields["fe8"]
    point_records = tuple({"kind": 0, "point": point.f} for point in points)
    line_records = tuple({"flags": 0, "line": line.f} for line in lines)
    del sketch.f["points"]
    del sketch.f["lines"]
    sketch.f.derived["points"] = lambda: point_records
    sketch.f.derived["lines"] = lambda: line_records
    del sketch.f["f130"]
    sketch.f.derived["f130"] = lambda: len(lines) + 1
    del sketch.f["f56c"]
    sketch.f.derived["f56c"] = lambda: len(lines) + 1
    counters = dict(sketch["f140"])
    del counters["f08"]
    del counters["f0c"]
    sketch["f140"] = DerivedFields(fields=counters, derived={"f08": lambda: len(points) + 1, "f0c": lambda: len(lines) + 1})
    sketch["_point_nodes"] = points
    sketch["_line_nodes"] = lines
    _bind_local_ref_flag(sketch=sketch)
    sketch["_requires_update"] = True
    return graph
