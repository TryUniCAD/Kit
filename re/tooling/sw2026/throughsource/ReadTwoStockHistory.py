from dataclasses import dataclass
from math import isclose, sqrt
from struct import unpack

from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import (
    CheckCutScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheBody import (
    ReadCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import (
    ReadCacheFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import (
    ReadStockData,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtoms import (
    ReadStockAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
    ReadStockOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
    ReadStockRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut import (
    ReadTwoStockCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

SCHEMA = "SCH_3701250_37102_13006"
LIMIT = 4096


@dataclass(frozen=True)
class Ref:
    field: str
    ordinal: int
    index: int
    at_or_below_limit: bool


@dataclass(frozen=True)
class Row:
    node: XmtNode
    refs: tuple[Ref, ...]


@dataclass(frozen=True)
class Frame:
    mark: XmtNode
    restored: tuple[Row, ...]
    removed: tuple[tuple[int, int], ...]
    copy_capacity: int
    changed: tuple[Row, ...]
    offset: int


@dataclass(frozen=True)
class Body:
    slot: int
    atom: int
    feature: int
    label: str
    tag: int
    faces: tuple[tuple[str, str], ...]
    points: tuple[tuple[float, float, float], ...]
    cylinders: tuple[tuple[tuple[float, ...], tuple[float, ...], float], ...]


@dataclass(frozen=True)
class State:
    mark_id: int
    world: XmtNode
    nodes: dict[int, XmtNode]
    bodies: tuple[Body, ...]


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def read_row(cursor, kind):
    require(
        kind in KKernelShapes and kind not in (3, 4), "unknown rollback owner class"
    )
    shape = KKernelShapes[kind]
    if kind not in cursor.SeenKinds:
        cursor.ExpectBytes(SchemaHeader(shape))
        cursor.SeenKinds.add(kind)
    size = (
        cursor.ReadCount()
        if any(field.CountValue == 1 for field in shape.FieldsValue)
        else 0
    )
    index = cursor.ReadIndex()
    require(index and size <= LIMIT, "invalid rollback record index or array count")
    fields, refs = {}, []
    for field in shape.FieldsValue:
        count = size if field.CountValue == 1 else field.CountValue
        if field.EncodingValue == "c":
            value = cursor.TakeBytes(count if field.CountValue else 1)
            fields[field.NameValue] = value if kind == 84 else value.decode("ascii")
            continue
        values = []
        for ordinal in range(count if field.CountValue else 1):
            value = ReadXmtValueMut(cursor, field)
            values.append(value)
            if field.EncodingValue == "p":
                (flag,) = cursor.TakeBytes(1)
                require(
                    flag in (0, 1) and (value != 0 or flag == 1),
                    "invalid qualified kernel reference",
                )
                refs.append(Ref(field.NameValue, ordinal, value, bool(flag)))
        fields[field.NameValue] = tuple(values) if field.CountValue else values[0]
    return Row(XmtNode(index, kind, fields), tuple(refs))


def read_rows(cursor):
    rows = []
    while (kind := cursor.ReadKind()) != 1:
        require(len(rows) < LIMIT, "rollback record list exceeds bounded size")
        rows.append(read_row(cursor, kind))
    require(cursor.ReadIndex() == 0, "rollback record list lacks its null terminator")
    return tuple(rows)


def decode_history(payload):
    header = ParaHeaderData(payload)
    require(
        header is not None
        and header.schema == SCHEMA
        and header.description
        == ": TRANSMIT FILE (deltas) created by modeller version 3701250",
        "unsupported rollback transmit profile",
    )
    cursor = XmtCursor(payload[header.body_offset :])
    require(cursor.ReadKind() == 3, "rollback stream has no PARTITION owner")
    root = ReadXmtNodeMut(cursor, 3)
    frames = {}
    while (kind := cursor.ReadKind()) != 1:
        require(kind == 4 and len(frames) < 5, "unexpected two stock PMARK inventory")
        mark = ReadXmtNodeMut(cursor, 4)
        offset = header.body_offset + cursor.OffsetValue
        require(mark.IndexValue not in frames, "duplicate PMARK transmit identity")
        if mark.Integer("delta_key"):
            restored = read_rows(cursor)
            removed = []
            while index := cursor.ReadIndex():
                kind = cursor.ReadKind()
                require(
                    kind in KKernelShapes
                    and kind not in (3, 4)
                    and len(removed) < LIMIT,
                    "unknown rollback deletion class or count",
                )
                removed.append((index, kind))
            (capacity,) = unpack(">i", cursor.TakeBytes(4))
            require(
                0 <= capacity <= LIMIT, "rollback copy capacity is outside its domain"
            )
            changed = read_rows(cursor)
            require(
                len(changed) <= capacity,
                "rollback changed rows exceed staging capacity",
            )
            frame = Frame(mark, restored, tuple(removed), capacity, changed, offset)
        else:
            frame = Frame(mark, (), (), 0, (), offset)
        frames[mark.IndexValue] = frame
    cursor.FinishRead()
    return root, frames


def actual_profile(archive):
    link = ReadNativeLink(archive, 0)
    features = ReadStockRoots(link)
    first, second, cut = ReadStockOps(link, features)
    root = RequireNative(link.ConfigValue.RootValue, "moPart_c")
    atoms = ReadStockAtoms(link, first.NodeValue, second.NodeValue, cut.NodeValue)
    require(
        atoms.SelectedIndex == 0,
        "two stock profile consumes a different blind producer",
    )
    source_atoms = (atoms.ConsumedAtom, atoms.UntouchedAtom, atoms.ResultAtom)
    roles = (first, second, cut)
    owners = {
        ReadCutAtomId(atom, role.NodeValue): (atom, role.NodeValue)
        for atom, role in zip(source_atoms, roles, strict=True)
    }
    scope = CheckCutScope(
        root, first.NodeValue, cut.NodeValue, next(iter(owners)), StockScope=0
    )
    if scope:
        actual = ReadTwoStockCut(link)
        require(
            actual.AtomsValue == atoms,
            "selected scope does not own the rolled back producer",
        )
    else:
        require(
            cut.NodeValue.FieldsValue.get("f548") is None,
            "unrestricted cut retains a selected body wrapper",
        )
    owners_of_marks = (
        root.FieldsValue.get("fe38"),
        *(role.NodeValue.FieldsValue.get("f3d0") for role in roles),
    )
    marks = tuple(RequireNative(node, "moPMarkRecord_c") for node in owners_of_marks)
    CheckTreeAlias(link, marks)
    ids = tuple(mark.FieldsValue.get("f18") for mark in marks)
    require(
        all(set(mark.FieldsValue) == {"f18"} for mark in marks)
        and all(type(value) is int and value > 1 for value in ids)
        and tuple(sorted(set(ids))) == ids,
        "ambiguous source feature mark selector",
    )
    return link, features, roles, owners, marks, ids, scope


def ordered_frames(root, frames, active, ids):
    world = RequireXmt(active, 1, 101)
    require(
        root.IndexValue not in frames
        and root.IndexValue not in active
        and not frames.keys() & active.keys(),
        "history header and active transmit identities overlap",
    )
    require(
        root.Integer("highest_id") == world.Integer("highest_id")
        and world.Integer("current_id") == ids[-1] <= root.Integer("highest_id"),
        "history current selector differs from the active world",
    )
    matches = (1, *ids)
    require(len(frames) == len(matches), "history has missing or additional marks")
    key = root.Integer("current_pmark")
    following = 0
    seen_keys = set()
    ordered = []
    for expected in reversed(matches):
        require(key in frames, "history predecessor is unresolved")
        frame = frames[key]
        mark = frame.mark
        require(
            mark.IndexValue == key
            and mark.KindValue == 4
            and mark.Integer("id") == expected
            and mark.Integer("first_following") == following
            and not any(
                mark.Integer(name)
                for name in ("next_sibling", "prev_sibling", "delta_is_forward")
            ),
            "history mark differs from actual chronological owner",
        )
        delta = mark.Integer("delta_key")
        counts = tuple(
            mark.Integer(name)
            for name in ("n_new_nodes", "n_del_nodes", "n_copy_mod_nodes")
        )
        require(
            all(0 <= count <= LIMIT for count in counts)
            and len(frame.removed) <= counts[0]
            and len(frame.restored) <= counts[1]
            and counts[2] <= frame.copy_capacity,
            "mark header counts disagree with physical rollback lists",
        )
        if expected == 1:
            require(
                not delta
                and not any(counts)
                and not frame.copy_capacity
                and not frame.changed,
                "initial mark unexpectedly owns a delta",
            )
        else:
            require(
                delta > 0 and delta not in seen_keys,
                "rollback handle is missing or repeated",
            )
            seen_keys.add(delta)
        ordered.append(frame)
        following, key = key, mark.Integer("preceding")
    require(not key, "initial mark has a foreign predecessor")
    return tuple(ordered)


def undo(current, frame, marks):
    removed = dict(frame.removed)
    restored = {row.node.IndexValue: row.node for row in frame.restored}
    changed = {row.node.IndexValue: row.node for row in frame.changed}
    require(
        len(removed) == len(frame.removed)
        and len(restored) == len(frame.restored)
        and len(changed) == len(frame.changed)
        and not removed.keys() & changed.keys()
        and not restored.keys() & (current.keys() | marks)
        and all(
            index in current and current[index].KindValue == kind
            for index, kind in removed.items()
        )
        and all(
            index in current and current[index].KindValue == node.KindValue
            for index, node in changed.items()
        ),
        "rollback slots overlap or differ from their actual current class",
    )
    require(
        len(changed) <= frame.copy_capacity and 1 not in removed and 1 in changed,
        "rollback copy capacity or retained WORLD differs",
    )
    previous = {index: node for index, node in current.items() if index not in removed}
    previous.update(restored)
    previous.update(changed)
    qualifiers = {}
    for row in (*frame.restored, *frame.changed):
        expected = []
        for field in KKernelShapes[row.node.KindValue].FieldsValue:
            if field.EncodingValue != "p":
                continue
            values = (
                row.node.Indexes(field.NameValue)
                if field.CountValue
                else (row.node.Integer(field.NameValue),)
            )
            expected.extend(
                (field.NameValue, ordinal, value)
                for ordinal, value in enumerate(values)
            )
        require(
            expected == [(ref.field, ref.ordinal, ref.index) for ref in row.refs],
            "rollback qualifiers do not cover their actual pointer owners",
        )
        for ref in row.refs:
            require(
                type(ref.at_or_below_limit) is bool
                and (ref.index or ref.at_or_below_limit)
                and ref.at_or_below_limit
                == qualifiers.setdefault(ref.index, ref.at_or_below_limit),
                "inconsistent source-index selector for a rollback target",
            )
    verify_graph(previous)
    return previous


def verify_graph(nodes):
    world = RequireXmt(nodes, 1, 101)
    require(
        sum(node.KindValue == 101 for node in nodes.values()) == 1
        and all(
            index in nodes for node in nodes.values() for index in XmtReferences(node)
        ),
        "rollback previous graph has orphaned native references",
    )
    for node in nodes.values():
        for field in KKernelShapes[node.KindValue].FieldsValue:
            if field.EncodingValue != "p" or field.PointerClass not in KKernelShapes:
                continue
            values = (
                node.Indexes(field.NameValue)
                if field.CountValue
                else (node.Integer(field.NameValue),)
            )
            for value in values:
                if value:
                    RequireXmt(nodes, value, field.PointerClass)
    return world


def vectors(value):
    return tuple(round(component, 9) for component in value)


def world_point(frame, x, y, z):
    return vectors(
        tuple(
            getattr(frame.origin, coord)
            + x * getattr(frame.x_axis, coord)
            + y * getattr(frame.y_axis, coord)
            + z * getattr(frame.z_axis, coord)
            for coord in ("x", "y", "z")
        )
    )


def body_slots(nodes, world, owners):
    indexes = WalkXmtChain(
        nodes, world.Integer("body"), 12, OwnerField="owner", OwnerValue=1
    )
    require(
        set(indexes)
        == {node.IndexValue for node in nodes.values() if node.KindValue == 12},
        "rollback WORLD body ownership is incomplete",
    )
    results = []
    all_faces = set()
    for index in indexes:
        node = nodes[index]
        owner = ReadCacheBody(nodes, node, owners)
        vertex_ids = WalkXmtChain(
            nodes, node.Integer("vertex"), 18, OwnerField="owner", OwnerValue=index
        )
        require(
            set(vertex_ids)
            == {
                value.IndexValue
                for value in nodes.values()
                if value.KindValue == 18 and value.Integer("owner") == index
            },
            "rollback stock vertex chain is incomplete",
        )
        points = tuple(
            sorted(
                vectors(
                    component * 1000
                    for component in RequireXmt(
                        nodes, nodes[vertex].Integer("point"), 29
                    ).FieldsValue["pvec"]
                )
                for vertex in vertex_ids
            )
        )
        faces = ReadCacheFaces(nodes, node)
        require(not all_faces & faces.keys(), "rollback body faces are cross-owned")
        all_faces.update(faces)
        carriers = (
            nodes[int(value.rsplit(":", 1)[1]) - 1]
            for value in sorted(set(faces.values()))
        )
        cylinders = tuple(
            (
                vectors(value * 1000 for value in carrier.FieldsValue["pvec"]),
                vectors(carrier.FieldsValue["axis"]),
                carrier.FieldsValue["radius"] * 1000,
            )
            for carrier in carriers
            if carrier.KindValue == 51
        )
        results.append(
            Body(
                index,
                owner.AtomId,
                NativeNodeId(owner.ProducerValue),
                owner.NameValue,
                owner.AtomValue.FieldsValue["f180"],
                tuple(sorted(faces.items())),
                points,
                cylinders,
            )
        )
    require(
        len(all_faces) == sum(node.KindValue == 14 for node in nodes.values()),
        "rollback graph retains detached native faces",
    )
    return tuple(results)


def require_geometry(link, features, roles, states):
    part = link.ConfigValue.RootValue
    frames = tuple(
        ReadPrismFrame(role.ProfileValue, part, features, FrontOnly=False)
        for role in roles
    )
    require(
        frames[0] == frames[2] and frames[1] != frames[0],
        "alternate two stock geometry frame",
    )
    loops = tuple(ReadThruStock(role.ProfileValue, link) for role in roles[:2])
    points = tuple(
        tuple(point.PositionValue for point in loop.PointsValue.values())
        for loop in loops
    )
    depths = tuple(role.RequireDepth().DepthValue.value_mm for role in roles[:2])
    before = states[1].bodies
    untouched, old, solitary = before[0], before[1], states[2].bodies[0]
    final_untouched, result = states[0].bodies
    require(
        untouched == final_untouched
        and old == solitary
        and old.slot == result.slot
        and old.tag == result.tag,
        "rollback changes the untouched stock or its consumed/result slot",
    )
    for own, frame, corners, depth in zip(
        (old, untouched), frames[:2], points, depths, strict=True
    ):
        expected = tuple(
            sorted(world_point(frame, x, y, z) for x, y in corners for z in (0, depth))
        )
        require(
            own.points == expected and len(own.faces) == 6 and not own.cylinders,
            "rollback stock geometry does not follow its linked profile and D1",
        )
    sketch = RequireNative(roles[2].ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    circle = ReadLocalCirc(sketch, link, AllowFree=True)
    require(
        circle is not None and circle[1] is None and len(result.cylinders) == 1,
        "result lacks the actual free-circle notch",
    )
    x_center, y_center = circle[0].CenterValue
    radius = circle[0].RadiusValue
    x0, x1 = min(x for x, _ in points[0]), max(x for x, _ in points[0])
    y0, y1 = min(y for _, y in points[0]), max(y for _, y in points[0])
    require(
        y0 < y_center - radius < y1 < y_center,
        "unsupported rectangle/circle intersection",
    )
    dx = sqrt(radius**2 - (y1 - y_center) ** 2)
    require(
        x0 < x_center - dx < x_center + dx < x1, "notch does not lie on one stock edge"
    )
    expected_points = set(old.points)
    expected_points.update(
        world_point(frames[2], x_center + shift, y1, z)
        for shift in (-dx, dx)
        for z in (0, depths[0])
    )
    origin, axis, actual_radius = result.cylinders[0]
    normal = frames[2].z_axis
    require(
        set(result.points) == expected_points
        and len(result.points) == len(expected_points)
        and len(result.faces) == len(old.faces) + 2
        and isclose(actual_radius, radius, rel_tol=0, abs_tol=1e-9)
        and isclose(
            abs(
                sum(
                    a * b
                    for a, b in zip(axis, (normal.x, normal.y, normal.z), strict=True)
                )
            ),
            1.0,
            rel_tol=0,
            abs_tol=1e-9,
        ),
        "cut result does not match its independent circle and stock geometry",
    )
    expected_origin = world_point(frames[2], x_center, y_center, 0)
    for direction in (frames[2].x_axis, frames[2].y_axis):
        distance = sum(
            (a - b) * n
            for a, b, n in zip(
                origin,
                expected_origin,
                (direction.x, direction.y, direction.z),
                strict=True,
            )
        )
        require(
            isclose(distance, 0, rel_tol=0, abs_tol=1e-9),
            "cut carrier does not follow its true circle centre",
        )


def require_body_events(events, states):
    world_slot = states[0].world.IndexValue
    moving_slot, cut_slot = (body.slot for body in states[0].bodies)
    stock_slot = states[2].bodies[0].slot
    require(cut_slot == stock_slot, "cut does not reuse its consumed stock slot")
    changed_sets = tuple(
        {row.node.IndexValue for row in event.changed} for event in events
    )
    require(
        {world_slot, moving_slot, cut_slot} <= changed_sets[0]
        and changed_sets[1:]
        == ({world_slot, stock_slot}, {world_slot}, {world_slot}, set()),
        "rollback histories differ from their WORLD and live body changes",
    )
    removed_bodies = tuple(
        {index for index, kind in event.removed if kind == 12} for event in events
    )
    require(
        removed_bodies == (set(), {moving_slot}, {stock_slot}, set(), set())
        and not any(
            row.node.KindValue == 12 for event in events for row in event.restored
        )
        and not any(event.restored for event in events[1:])
        and not events[3].removed
        and all(event.copy_capacity == len(event.changed) for event in events[1:]),
        "rollback BODY events differ from the actual independent stock lifecycles",
    )


def verify_history(archive, active, root, frames):
    link, features, roles, owners, owner_marks, ids, scope = actual_profile(archive)
    consumed, untouched, result = tuple(owners)
    expected = ((untouched, result), (untouched, consumed), (consumed,), (), ())
    ordered = ordered_frames(root, frames, active, ids)
    reserved = {root.IndexValue, *frames}
    registry = {
        index: node for index, node in active.items() if node.KindValue in (79, 80)
    }
    expected_definitions = WalkXmtChain(
        active, active[1].Integer("attrib_def"), 80, PreviousField=None
    )
    require(
        set(expected_definitions)
        == {index for index, node in registry.items() if node.KindValue == 80}
        and {active[index].Integer("identifier") for index in expected_definitions}
        == {index for index, node in registry.items() if node.KindValue == 79},
        "active attribute registry is incomplete",
    )
    current = active
    states = []
    for order, (frame, wanted) in enumerate(zip(ordered, expected, strict=True)):
        world = verify_graph(current)
        require(
            all(current.get(index) == node for index, node in registry.items())
            and world.Integer("alive") == int(order != len(ordered) - 1)
            and (
                not order
                or not any(
                    world.Integer(field)
                    for field in ("attrib_def", "current_id", "highest_id")
                )
            )
            and (wanted or set(current) == {1, *registry}),
            "rollback WORLD activation or global registry differs",
        )
        bodies = body_slots(current, world, owners)
        require(
            tuple(body.atom for body in bodies) == wanted,
            "rollback body order/count disagrees with its physical producer",
        )
        states.append(State(frame.mark.Integer("id"), world, current, bodies))
        if frame.mark.Integer("delta_key"):
            current = undo(current, frame, reserved)
    require_body_events(ordered, states)
    require_geometry(link, features, roles, states)
    return tuple(states), ordered, owner_marks, scope


def read_history(archive):
    name = "Contents/Config-0-Partition"
    active, _ = ReadStockData(archive, name)
    _, delta = DecodePartData(archive.require(name), name)
    root, frames = decode_history(delta.data)
    return verify_history(archive, active, root, frames)
