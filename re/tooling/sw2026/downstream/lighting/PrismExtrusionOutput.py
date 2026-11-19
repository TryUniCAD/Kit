from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from para.concentric.CylinderFace import words


def read_prism_output(archive, partition):
    linked = ReadNativeLink(archive, 0)
    model = linked.ConfigValue.RootValue
    manager = model.FieldsValue["fd88"]
    atom, = (row["o"] for row in manager["atoms"])
    feature, = (root for root in linked.ResolvedValue.RootsValue
                if root is not None and root.ClassValue.NameValue == "moExtrusion_c")
    nodes = {node.index: node for node in partition.nodes}
    body, = (node for node in nodes.values() if node.kind == 12)
    atom_id, = words(nodes, body, "ATOM_ID_2001", 1)
    match_tag, = words(nodes, body, "BODY_MATCH", 0)
    producer_id, = words(nodes, body, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
    atom_fields = atom.FieldsValue
    if (model.ClassValue.NameValue != "moPart_c" or atom.ClassValue.NameValue != "moAtom_c"
            or not 0 < atom_id < 1 << 31
            or atom_id != manager["f260"] or atom_id != atom_fields["f140"]
            or match_tag != atom_fields["f180"] or match_tag != atom_fields["f1b0"]
            or producer_id != feature.FieldsValue["f08"]
            or producer_id != atom_fields["f12c"] or producer_id != atom_fields["f130"]):
        raise ValueError("generated prism body, manager and producing extrusion disagree")
    return linked, atom, feature, body.index


def link_prism_output(archive, partition):
    linked, atom, feature, index = read_prism_output(archive, partition)
    fields = feature.FieldsValue
    if (fields["has_f528"] or fields["has_f530"] or fields["n494"]
            or fields["f498"] or fields["f538"] is not None):
        raise ValueError("generated prism already has an output or modification atom")
    outputs = [{"o": atom}]
    fields.update(
        has_f528=1,
        f528={"n": len(outputs), "items": outputs},
        n494=len(outputs),
        f498=[{"v": row["o"].FieldsValue["f140"]} for row in outputs],
    )
    resolved, _ = WriteResolMut(
        linked.ResolvedValue.RootsValue,
        linked.ResolvedValue.ExtraFields,
        linked.ConfigValue.VersionValue,
        linked.ConfigValue.MapValue,
        linked.ResolvedValue.ContextValue,
    )
    return archive.streams | {KResolvedFeaturesStream: resolved}, index


def verify_prism_output(archive, partition, expected_index):
    _, atom, feature, index = read_prism_output(archive, partition)
    fields = feature.FieldsValue
    outputs = fields["f528"]
    atom_id = atom.FieldsValue["f140"]
    if (index != expected_index or outputs["n"] != 1 or len(outputs["items"]) != 1
            or outputs["items"][0]["o"] is not atom or fields["n494"] != 1
            or fields["f498"] != [{"v": atom_id}]):
        raise ValueError("linked readback lost the actual generated extrusion output")
    return {"atom_id": atom_id, "producer_id": fields["f08"], "active_body_index": index}
