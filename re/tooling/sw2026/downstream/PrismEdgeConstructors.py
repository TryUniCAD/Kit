from dataclasses import dataclass

from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.CacheInputs import ARCHIVE_VERSION
from downstream.EdgeOperands import prism_edge_operands
from downstream.PrismFaceConstructors import ordinary_prism_component_fields, read_prism_face_owners
from downstream.PrismFaceStore import ordinary_surface_description, prism_face_store_fields, surface_key_hash
from para.Partition import read_partition
from para.concentric.CylinderFace import node


@dataclass(frozen=True)
class EdgeKey:
    row_id: int
    original: int
    anti: int


def make_prism_edge_constructor(operand, surfaces, owners):
    inline_ids = [{"f08": surfaces[face_id]} for face_id in operand.role_face_ids]
    data = {
        "f10": [{"key": role, "value": face_id} for role, face_id in enumerate(operand.role_face_ids)],
        "f20": [], "f38": 0, "f40_0": 0, "f40_1": 0,
    }
    reference = node("moEdgeRef_c", {
        "f60": 1, "f64": 0, "f08": len(inline_ids), "fe8": 0x300, "f70": 0,
        "f28": 1e100, "f30": 1e100, "f40": None, "f10": inline_ids,
        "f48": 0, "nd0": 0, "fd0": [], "fec": ARCHIVE_VERSION,
        "has_f18": 1, "f18": data,
    })
    origin = dict.fromkeys(("x", "y", "z"), 0.0)
    component = ordinary_prism_component_fields(owners, reference) | {
        "f188": 0, "f18c": 0, "f158": origin, "f170": dict(origin), "f130": [],
    }
    return {"object": node("moCompEdge_c", component), "word": operand.downstream_id}


def prism_edge_keys(rows):
    registered = set()
    keys = []
    for row in rows:
        component = row["object"].FieldsValue
        reference = component["fe8"].FieldsValue
        inline = tuple(slot["f08"] for slot in reference["f10"])
        if (component["f68"] != 0 or reference["fe8"] != 0x300 or reference["f70"] != 0
                or len(inline) != 4 or any(rep is None for rep in inline)):
            raise ValueError("edge-key storage requires the ordinary four-surface mode-one constructor")
        descriptions = tuple(map(ordinary_surface_description, inline))
        if len(set(descriptions)) != 4:
            raise ValueError("edge-key storage requires four distinct surfaces before anti-copy")
        left, right, start, end = descriptions
        original = surface_key_hash("s," + left + right + start + end)
        anti = surface_key_hash("s," + right + left + end + start)
        if not original or original in registered or anti in registered:
            raise ValueError("edge-key storage requires the native noncollision path")
        keys.append(EdgeKey(row["word"], original, anti))
        registered.add(original)
    return tuple(keys)


def prism_edge_constructor_fields(archive, allocation, *, special_id_map_present):
    fields, _ = prism_face_store_fields(archive, allocation, special_id_map_present=special_id_map_present)
    partition = read_partition(archive.require(KPartitionStream))
    owners = read_prism_face_owners(archive, partition)
    operands = prism_edge_operands(
        partition, allocation, owners.HeaderValue.FieldsValue["f48"],
        special_id_map_present=special_id_map_present,
    )
    surfaces = {
        row["word"]: row["object"].FieldsValue["fe8"].FieldsValue["f10"][0]["f08"]
        for row in fields["f48"]
    }
    if {id(surface) for surface in surfaces.values()} != {id(row["object"]) for row in fields["f40"]}:
        raise ValueError("prism edge operands require the retained face rows and their collected surfaces")
    rows = [make_prism_edge_constructor(operand, surfaces, owners) for operand in operands]
    return fields | {"f60": rows}, prism_edge_keys(rows)
