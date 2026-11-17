from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from Core import Obj
from builders.EmptyPartition import INITIAL_PMARK_ID, PARTITION_KIND, PMARK_KIND, WORLD_KIND
from builders.Model import node_list
from para.Partition import Node
from para.Tracking import body_match_tag, local_downstream_face_words, unchanged_face_stamp, unsigned


class Update(Enum):
    ADVANCE = "advance update"
    TESSELLATE = "stamp tessellated faces"
    ADVANCE_BODY = "advance body stamp"
    ATTACH_BODY = "stamp attached body"


@dataclass(frozen=True)
class DeltaEvent:
    name: str


@dataclass(frozen=True)
class MarkEvent:
    name: str
    delta: str
    retain: bool


@dataclass(frozen=True)
class Mark:
    name: str
    mark_id: int
    delta_key: int


@dataclass(frozen=True)
class Marks:
    initial: Mark
    activation: Mark
    selected: Mark

    @property
    def kernel_index_order(self):
        return (self.selected, self.activation, self.initial)

    @property
    def transmit_order(self):
        return (self.selected, self.initial, self.activation)


@dataclass(frozen=True)
class Updates:
    face: int
    body: int
    saved_update: int
    saved_body: int
    downstream: tuple[int, ...]


@dataclass(frozen=True)
class Session:
    first_tag: int
    next_delta_handle: int
    mark_events: tuple[DeltaEvent | MarkEvent, ...]
    update_events: tuple[Update, ...]
    update_second: int
    update_fraction: int


@dataclass(frozen=True)
class Ref:
    name: str


@dataclass(frozen=True)
class DraftNode:
    ref: Ref
    kind: int
    fields: Mapping


@dataclass(frozen=True)
class ArchiveBinding:
    part_mark: Obj
    feature_mark: Obj
    atom: Obj
    manager_registration: Mapping
    active_header_fields: Mapping
    feature_id: int


@dataclass(frozen=True)
class Tracking:
    body_tag: int
    face_tags: Mapping[str, int]
    body_fields: Mapping
    face_fields: Mapping


@dataclass(frozen=True)
class IndexedDraft:
    active: tuple[Node, ...]
    partition: Node
    marks: tuple[Node, ...]
    previous_worlds: tuple[Node, ...]
    geometry_rollback_members: tuple[tuple[int, int], ...]


class IncompletePartition(ValueError):
    pass


def require(value, message):
    if not value:
        raise ValueError(message)


def positive_i32(value, owner):
    require(type(value) is int and 0 < value < 1 << 31, f"{owner} requires a positive signed i32")
    return value


def allocate_marks(session):
    next_delta = positive_i32(session.next_delta_handle, "next delta handle")
    initial = Mark("initial", INITIAL_PMARK_ID, 0)
    retained = [initial]
    allocated = {}
    marked = {"initial"}
    consumed = set()
    mark_id = initial.mark_id
    for event in session.mark_events:
        if isinstance(event, DeltaEvent):
            require(isinstance(event.name, str) and event.name and event.name not in allocated,
                    "delta allocation names must be unique and nonempty")
            allocated[event.name] = positive_i32(next_delta, "delta key")
            next_delta += 1
            continue
        require(isinstance(event, MarkEvent) and isinstance(event.name, str) and event.name
                and event.name not in marked and type(event.retain) is bool,
                "mark events require unique names and an explicit retention state")
        require(event.delta in allocated and event.delta not in consumed,
                "each new mark must own an independently allocated delta handle")
        marked.add(event.name)
        consumed.add(event.delta)
        mark_id = positive_i32(mark_id + 1, "mark id")
        if event.retain:
            retained.append(Mark(event.name, mark_id, allocated[event.delta]))
    require([mark.name for mark in retained] == ["initial", "activation", "geometry"]
            and retained[-1].mark_id == mark_id, "rectangle history must retain activation and selected geometry")
    return Marks(*retained)


def allocate_updates(session, model_header):
    update = unsigned(model_header["f40"], 32, "initial update counter")
    body = unsigned(model_header["f44"], 32, "initial body counter")
    face_stamp = None
    body_stamp = None
    for operation in session.update_events:
        if operation is Update.ADVANCE:
            update = unsigned(update + 1, 32, "marked update counter")
        elif operation is Update.ADVANCE_BODY:
            body = unsigned(body + 1, 32, "body counter")
        elif operation is Update.ATTACH_BODY:
            require(body_stamp is None, "the rectangle owns one attached body")
            body = unsigned(body + 1, 32, "attached body counter")
            body_stamp = body
        elif operation is Update.TESSELLATE:
            require(body_stamp is not None and face_stamp is None, "the rectangle needs one face-stamp event after body attachment")
            face_stamp = update
        else:
            raise ValueError("unspecified model update event")
    require(face_stamp is not None and body_stamp is not None, "the body and face assignment events are required")
    stamp = local_downstream_face_words(session.update_second, session.update_fraction)
    return Updates(face_stamp, body_stamp, update, body, stamp)


def allocate_tracking(child, geometry, session, marks, updates):
    boss = child.extrusion.feature
    feature_id = positive_i32(boss["f08"], "extrusion feature")
    atom_id = positive_i32(child.model["fd88"]["f260"] + 1, "next model atom")
    body_tag = positive_i32(session.first_tag, "first kernel entity tag")
    face_tags = {face.id: positive_i32(body_tag + offset, "face tag") for offset, face in enumerate(geometry.faces, 1)}
    body_name = boss["f18"]["f08"]
    require(isinstance(body_name, str) and body_name and "\x00" not in body_name, "implicit body name needs an authored feature name")
    body_name_u16 = tuple(int.from_bytes(unit, "little") for unit in chunks(body_name.encode("utf-16-le"), 2))
    body_tracking = {
        "BODY_MATCH": (body_match_tag(body_tag),),
        "ATOM_ID_2001": (None, atom_id),
        "ENT_TIME_STAMP_2001": (None, updates.body),
        "LAST_BODY_MODIFYING_FEATURE_ID": (None, feature_id),
        "SWIMPLICITBODYNAME_ID_U": (body_name_u16, None),
    }
    face_tracking = {
        face_id: {
            "SWEntUnchanged": (unchanged_face_stamp(tag, updates.face),),
            "DOWNSTREAM_FACE_ID": (updates.downstream, None, None),
        }
        for face_id, tag in face_tags.items()
    }
    atom = Obj("moAtom_c", {
        "f18": None,
        "f0c": 1,
        "f28": 0x40000000,
        "f08": -1,
        "f2c": 0,
        "f20": "",
        "has_list68": 0,
        "f78": None,
        "f60": node_list(),
        "f140": atom_id,
        "f144": 0,
        "f12c": feature_id,
        "f130": feature_id,
        "f158": 0,
        "body_kind": 0,
        "f170": 0,
        "f18c": 1,
        "f198": -1,
        "f180": body_match_tag(body_tag),
        "f1b0": body_match_tag(body_tag),
        "f188": int(geometry.regions[0].solid),
        "f19c": 6,
    }, schema=1)
    archive = ArchiveBinding(
        part_mark=Obj("moPMarkRecord_c", {"f18": marks.activation.mark_id}, schema=1),
        feature_mark=Obj("moPMarkRecord_c", {"f18": marks.selected.mark_id}, schema=1),
        atom=atom,
        manager_registration={
            "f260": atom_id,
            "atoms": [{"o": atom}],
            "fa8": child.model["fd88"]["fa8"],
        },
        active_header_fields={"f40": updates.saved_update, "f44": updates.saved_body, "f48": session.update_second},
        feature_id=feature_id,
    )
    return Tracking(body_tag, face_tags, body_tracking, face_tracking), archive


def chunks(data, width):
    return (data[index:index + width] for index in range(0, len(data), width))


def world(marks, body):
    return DraftNode(Ref("world"), WORLD_KIND, {
        "body": body,
        "alive": 1,
        "highest_id": marks.selected.mark_id,
        "current_id": marks.selected.mark_id,
    })


def index_fields(fields, indexes):
    def resolve(value):
        if isinstance(value, Ref):
            return indexes[value]
        if isinstance(value, tuple):
            return tuple(resolve(item) for item in value)
        return value

    return {name: resolve(value) for name, value in fields.items()}


def index_draft(known_nodes, marks):
    root_ref = Ref("partition")
    mark_refs = {mark.name: Ref(f"mark:{mark.name}") for mark in marks.kernel_index_order}
    allocation_order = (*[node.ref for node in known_nodes], root_ref,
                        *[mark_refs[mark.name] for mark in marks.kernel_index_order])
    indexes = {ref: index for index, ref in enumerate(allocation_order, 1)}
    require(len(indexes) == len(allocation_order) and indexes.get(Ref("world")) == 1,
            "wire indexes require unique named nodes and WORLD at one")
    active = tuple(Node(indexes[node.ref], node.kind, index_fields(node.fields, indexes)) for node in known_nodes)
    root = Node(indexes[root_ref], PARTITION_KIND, {
        "current_pmark": indexes[mark_refs[marks.selected.name]],
        "highest_id": marks.selected.mark_id,
    })
    initial, activation, selected = marks.initial, marks.activation, marks.selected
    links = {
        initial.name: (0, indexes[mark_refs[activation.name]]),
        activation.name: (indexes[mark_refs[initial.name]], indexes[mark_refs[selected.name]]),
        selected.name: (indexes[mark_refs[activation.name]], 0),
    }
    history = tuple(Node(indexes[mark_refs[mark.name]], PMARK_KIND, {
        "preceding": links[mark.name][0],
        "first_following": links[mark.name][1],
        "next_sibling": 0,
        "prev_sibling": 0,
        "delta_key": mark.delta_key,
        "delta_is_forward": 0,
        "id": mark.mark_id,
    }) for mark in marks.transmit_order)
    previous_worlds = tuple(Node(indexes[Ref("world")], WORLD_KIND, {
        "body": 0, "alive": alive, "current_id": 0, "highest_id": 0,
    }) for alive in (1, 0))
    members = tuple((node.index, node.kind) for node in active if node.kind not in (WORLD_KIND, 79, 80))
    return IndexedDraft(active, root, history, previous_worlds, members)
