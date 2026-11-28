from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


FAULTS = {
    "later_producer": "does not identify an actual earlier stock producer",
    "mismatched_atom_key": "differs from the consumed boss atom",
    "retargeted_stock": "do not share their exact signed datum",
    "foreign_component_owner": "differs from the consumed boss atom",
    "detached_manager_atom": "contains missing or additional ownership",
    "reordered_manager_atoms": "disagree with their manager allocation",
    "wrong_allocator": "disagree with their manager allocation",
    "realized_stock_atom": "alternate node body tag or display state",
    "shared_depth": "share an actual driving depth owner",
    "renamed_depth": "lacks its actual typed D1",
    "detached_depth_display": "does not alias its archive map",
    "consumed_stock": "has a result, consumed atom or chooser owner",
    "invented_result": "has a result, consumed atom or chooser owner",
    "saved_face_carrier": "has an external or cached topology owner",
    "changed_profile_frame": "placement differs from its actual datum",
}


def detached(node):
    return ArchiveNode(
        node.ClassValue, dict(node.FieldsValue), node.StartOffset, node.EndOffset, node.IndexValue
    )


def damage(decoded, name):
    first, second, cut = decoded.OwnerValues
    link = decoded.LinkValue
    root = link.ConfigValue.RootValue
    wrapper = decoded.WrapperValue.FieldsValue
    manager = root.FieldsValue["fd88"]
    selected = decoded.SelectedIndex
    other = 1 - selected
    selected_atom = decoded.StockAtoms[selected]
    alternate_atom_id = decoded.StockAtoms[other].FieldsValue["f140"]
    if name == "later_producer":
        wrapper["f108"] = NativeNodeId(cut.NodeValue)
    elif name == "mismatched_atom_key":
        wrapper["f18"] = alternate_atom_id
    elif name == "retargeted_stock":
        wrapper.update(
            f108=NativeNodeId(decoded.OwnerValues[other].NodeValue),
            f18=alternate_atom_id, f1c=alternate_atom_id, f110=[{"v": alternate_atom_id}],
        )
    elif name == "foreign_component_owner":
        wrapper["f58"].FieldsValue["owner"] = detached(root)
    elif name == "detached_manager_atom":
        replacement = detached(selected_atom)
        manager["atoms"][selected]["o"] = replacement
        decoded.OwnerValues[selected].NodeValue.FieldsValue["f528"]["items"][0]["o"] = replacement
    elif name == "reordered_manager_atoms":
        manager["atoms"].reverse()
    elif name == "wrong_allocator":
        manager["f260"] += 1
    elif name == "realized_stock_atom":
        selected_atom.FieldsValue["f144"] = 1
    elif name == "shared_depth":
        second.EndValue.FieldsValue["f18"] = first.RequireDepth().DisplayValue
    elif name == "renamed_depth":
        first.RequireDepth().Parameter.FieldsValue["f18"].FieldsValue["f08"] = "D2"
    elif name == "detached_depth_display":
        first.EndValue.FieldsValue["f18"] = detached(first.RequireDepth().DisplayValue)
    elif name == "consumed_stock":
        cut.NodeValue.FieldsValue.update(has_f530=1, f530={"n": 1, "items": [{"o": selected_atom}]})
    elif name == "invented_result":
        cut.NodeValue.FieldsValue.update(has_f528=1, f528={"n": 1, "items": [{"o": selected_atom}]})
    elif name == "saved_face_carrier":
        wrapper["ff0"] = ArchiveNode(RuntimeClass("moFaceRef_c", 1), {})
    elif name == "changed_profile_frame":
        cut.ProfileValue.FieldsValue["pd_ff0"]["f58"] = 0.001
    else:
        raise ValueError(f"unknown ownership contrast {name}")
    return link
