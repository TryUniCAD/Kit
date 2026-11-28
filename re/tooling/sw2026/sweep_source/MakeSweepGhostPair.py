from dataclasses import dataclass
from math import isfinite

from convert.Geometry.Parasolid import EncodePartData
from convert.adapters.solidworks.Archive.Construction.Model.MakeModelSeeds import MakeModelSeeds
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeEmptyWorld import MakeEmptyWorld
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import MakePrismNodes
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from SweepGhostAttributes import body_attributes, definitions
from SweepGhostGraph import encode_ghost
from SweepModel import require
from SweepPathWire import make_path_nodes
from SweepSectionTransport import make_section_cells


MODEL = RuntimeClass("moPart_c", 1)
SWEEP = RuntimeClass("moSweep_c", 1)
FIRST_GHOST_BASE = MakeModelSeeds()["fd90"]["f80"]


@dataclass(frozen=True)
class GhostPair:
    section_id: int
    path_id: int
    manager: dict
    transmit: bytes
    stream: bytes


def role_rows(part, sweep):
    require(part.ClassValue == MODEL and sweep.ClassValue == SWEEP and sweep.FieldsValue.get("owner") is part,
            "ghost inputs must use the actual sweep and part owner")
    identifier = sweep.FieldsValue.get("f08")
    seed = part.FieldsValue.get("fd90")
    require(type(identifier) is int and 0 < identifier < 0x7fffffff and type(seed) is dict
            and set(seed) == {"f80", "fe0", "n", "objects"} and seed["f80"] == FIRST_GHOST_BASE
            and seed["fe0"] == seed["n"] == 0 and tuple(seed["objects"]) == (),
            "ghost construction requires a distinct allocated sweep and empty initial manager")
    section, path = (seed["f80"] + offset for offset in (1, 2))
    rows = tuple({"o": {"f08": value, "f0c": 8, "f10": 0, "fc0": -1,
                        "fa0": ({"v": identifier},), "has_f50": 0, "ff0": ()}}
                 for value in (path, section))
    return section, path, {"f80": path, "fe0": 2, "objects": rows}


def shift_cell(node, indices):
    original = node.FieldsValue
    fields = dict(original)
    for wire_field in KKernelShapes[node.KindValue].FieldsValue:
        if wire_field.EncodingValue != "p":
            continue
        value = original[wire_field.NameValue]
        fields[wire_field.NameValue] = (tuple(indices[member] for member in value)
                                        if wire_field.CountValue else indices[value])
    return XmtNode(indices[node.IndexValue], node.KindValue, fields)


def attach_shape(shape, first, following, previous, world, body_def, edge_def, ghost_id):
    root, *geometry = shape
    edge, = (node for node in geometry if node.KindValue == 16)
    require(root.KindValue == 12 and root.Integer("owner") == root.Integer("next") == root.Integer("previous") == 0,
            "ghost attachment requires a freshly computed isolated local graph")
    indices = {node.IndexValue: slot for slot, node in enumerate(shape, first)} | {0: 0}
    body, *moved = (shift_cell(node, indices) for node in shape)
    last_entity = body.Integer("highest_node_id")
    extras = body_attributes(first + len(shape), body.IndexValue, indices[edge.IndexValue],
                             last_entity, body_def, edge_def, ghost_id)
    body_attr, _, edge_attr, chain, _ = extras
    body.FieldsValue.update(owner=world, next=following, previous=previous, highest_node_id=last_entity + 2,
                            attributes_features=body_attr.IndexValue, attribute_chains=chain.IndexValue)
    indexed_edge, = (node for node in moved if node.IndexValue == indices[edge.IndexValue])
    indexed_edge.FieldsValue["attributes_features"] = edge_attr.IndexValue
    return body, *moved, *extras


def make_sweep_ghost_pair(part, sweep, section_radius, path_radius):
    require(all(type(value) in (int, float) and isfinite(value) for value in (section_radius, path_radius))
            and 0.001 <= section_radius < path_radius <= 0.15, "ghost inputs require measured positive nonintersecting radii")
    section_id, path_id, manager = role_rows(part, sweep)
    sheet = MakePrismNodes(make_section_cells(section_radius))
    wire = make_path_nodes(path_radius)
    world = MakeEmptyWorld(1, 1, len(manager["objects"]))
    body_def, edge_def, *names = definitions(world.IndexValue + 1)
    path_first = names[-1].IndexValue + 1
    path_cells = attach_shape(wire, path_first, path_first + len(wire) + 5, 0, world.IndexValue,
                              body_def.IndexValue, edge_def.IndexValue, path_id)
    section_first = path_cells[-1].IndexValue + 1
    section_cells = attach_shape(sheet, section_first, 0, path_first, world.IndexValue,
                                 body_def.IndexValue, edge_def.IndexValue, section_id)
    world.FieldsValue.update(attrib_def=body_def.IndexValue, body=path_first)
    cells = (world, body_def, edge_def, *names, *path_cells, *section_cells)
    indexed = {cell.IndexValue: cell for cell in cells}
    require(len(indexed) == len(cells), "ghost transmit assigned duplicate identities")
    transmit = encode_ghost(indexed)
    return GhostPair(section_id, path_id, manager, transmit, EncodePartData(transmit))
