from dataclasses import dataclass
from struct import pack

from convert.Geometry.Parasolid import EncodePartData, ParaStream, WritePointerMut


@dataclass(frozen=True)
class TransmitFormat:
    modeller_version: int
    schema_version: int
    embedding_base_schema: int
    maximum_node_types: int

    @property
    def schema(self):
        return f"SCH_{self.modeller_version}_{self.schema_version}_{self.embedding_base_schema}"


SOLIDWORKS_2026 = TransmitFormat(3701250, 37102, 13006, 239)
HISTORICAL_BLANK = TransmitFormat(3601228, 36001, 13006, 231)


@dataclass(frozen=True)
class EmptyHistory:
    current_pmark_id: int
    current_delta_key: int

    def __post_init__(self):
        if type(self.current_pmark_id) is not int or not 1 < self.current_pmark_id < 2**31:
            raise ValueError("the current pmark id must follow the initial pmark")
        if type(self.current_delta_key) is not int or not 0 < self.current_delta_key < 2**31:
            raise ValueError("the current pmark needs a positive delta handle")


@dataclass(frozen=True)
class Field:
    name: str
    encoding: str
    pointer_class: int = 0

    def descriptor(self, result):
        short_string(result, self.name)
        result.extend(pack(">H", self.pointer_class))
        WritePointerMut(result, 0)
        if self.pointer_class == 0:
            short_string(result, self.encoding)


def pointer(name, pointer_class):
    return Field(name, "p", pointer_class)


BASE_WORLD = (
    pointer("assembly", 10),
    pointer("attribute", 81),
    pointer("body", 12),
    pointer("transform", 100),
    pointer("surface", 1006),
    pointer("curve", 1008),
    pointer("point", 29),
    Field("alive", "l"),
    pointer("attrib_def", 80),
    Field("highest_id", "d"),
    Field("current_id", "d"),
)
WORLD = (
    *BASE_WORLD[:7],
    pointer("mesh", 1006),
    pointer("polyline", 1008),
    pointer("lattice", 222),
    *BASE_WORLD[7:9],
    pointer("attdef_list", 74),
    *BASE_WORLD[9:],
    Field("index_map_offset", "d"),
    pointer("index_map", 82),
    pointer("schema_embedding_map", 82),
    pointer("mesh_offset_data", 206),
)

PARTITION = (pointer("current_pmark", 4), Field("highest_id", "d"))
PMARK = (
    pointer("preceding", 4),
    pointer("first_following", 4),
    pointer("next_sibling", 4),
    pointer("prev_sibling", 4),
    Field("n_new_nodes", "d"),
    Field("n_del_nodes", "d"),
    Field("n_copy_mod_nodes", "d"),
    Field("delta_key", "d"),
    Field("delta_is_forward", "l"),
    Field("id", "d"),
)

WORLD_KIND = 101
PARTITION_KIND = 3
PMARK_KIND = 4
TERMINATOR_KIND = 1
INITIAL_PMARK_ID = 1


def short_string(result, text):
    encoded = text.encode("ascii")
    result.append(len(encoded))
    result.extend(encoded)


def write_schema_difference(result, base, current):
    if current == base:
        result.append(255)
        return
    result.append(len(current))
    base_index = current_index = 0
    while base_index < len(base) and current_index < len(current):
        base_field, current_field = base[base_index], current[current_index]
        if base_field == current_field:
            result.extend(b"C")
            base_index += 1
            current_index += 1
        elif base_field in current[current_index:]:
            result.extend(b"I")
            current_field.descriptor(result)
            current_index += 1
        else:
            result.extend(b"D")
            base_index += 1
    for field in current[current_index:]:
        result.extend(b"A")
        field.descriptor(result)
    result.extend(b"Z")


def write_node(result, kind, index, fields, state, *, base=None, delta_world=False):
    result.extend(pack(">H", kind))
    if base is not None:
        write_schema_difference(result, base, fields)
    WritePointerMut(result, index)
    for field in fields:
        value = state.get(field.name, 0)
        if field.encoding == "p":
            WritePointerMut(result, value)
            if delta_world:
                if value != 0:
                    raise ValueError("the initial world of an empty partition has no references")
                result.append(True)
        else:
            result.extend(pack(">B" if field.encoding == "l" else ">i", value))


def terminate(result):
    result.extend(pack(">H", TERMINATOR_KIND))
    WritePointerMut(result, 0)


def blank_partition_payloads(history, *, transmit_format=SOLIDWORKS_2026):
    if transmit_format not in (SOLIDWORKS_2026, HISTORICAL_BLANK):
        raise ValueError("this empty partition schema is unqualified")
    indexes = {
        node: index
        for index, node in enumerate(("world", "partition", "current", "initial"), start=1)
    }
    header_fields = pack(">HI", transmit_format.maximum_node_types, 0)
    highest_id = max(INITIAL_PMARK_ID, history.current_pmark_id)
    active_world = {
        "alive": True,
        "highest_id": highest_id,
        "current_id": history.current_pmark_id,
    }
    initial_world = {"alive": False, "highest_id": 0, "current_id": 0}

    partition = bytearray(header_fields)
    write_node(partition, WORLD_KIND, indexes["world"], WORLD, active_world, base=BASE_WORLD)
    terminate(partition)

    deltas = bytearray(header_fields)
    partition_state = {"current_pmark": indexes["current"], "highest_id": highest_id}
    write_node(deltas, PARTITION_KIND, indexes["partition"], PARTITION, partition_state, base=PARTITION)
    current_pmark = {
        "preceding": indexes["initial"],
        "delta_key": history.current_delta_key,
        "id": history.current_pmark_id,
    }
    write_node(deltas, PMARK_KIND, indexes["current"], PMARK, current_pmark, base=PMARK)
    terminate(deltas)
    WritePointerMut(deltas, 0)
    prior_worlds = (initial_world,)
    deltas.extend(pack(">i", len(prior_worlds)))
    for state in prior_worlds:
        write_node(deltas, WORLD_KIND, indexes["world"], WORLD, state, base=BASE_WORLD, delta_world=True)
    terminate(deltas)
    initial_pmark = {"first_following": indexes["current"], "id": INITIAL_PMARK_ID}
    write_node(deltas, PMARK_KIND, indexes["initial"], PMARK, initial_pmark)
    terminate(deltas)

    return tuple(
        ParaStream(
            body,
            transmit_format.schema,
            (
                f": TRANSMIT FILE ({kind}) created by modeller version "
                f"{transmit_format.modeller_version}"
            ).encode("ascii"),
        )
        for kind, body in (("partition", partition), ("deltas", deltas))
    )


def blank_partition_stream(history, *, transmit_format=SOLIDWORKS_2026):
    payloads = blank_partition_payloads(history, transmit_format=transmit_format)
    return b"".join(EncodePartData(payload) for payload in payloads)
