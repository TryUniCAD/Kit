from downstream.CacheInputs import topology_node


PERMANENT_EDGE_DEFINITION = "EDGE_PERM_ID_2001"


def permanent_edge_ids(partition):
    nodes = {node.index: node for node in partition.nodes}
    permanent = set()
    for attribute in partition.nodes:
        if attribute.kind != 81:
            continue
        definition = nodes[attribute.fields["definition"]]
        name = nodes[definition.fields["identifier"]].fields["string"]
        if name != PERMANENT_EDGE_DEFINITION:
            continue
        owner = nodes[attribute.fields["owner"]]
        if owner.kind != 16:
            raise ValueError("permanent edge identity has a foreign topology owner")
        permanent.add(owner.fields["node_id"])
    return permanent


def prepare_boundary_roles(topology, plan, partition, *, special_id_map_present):
    if special_id_map_present is not False:
        raise ValueError("ordinary boundary fallback requires the special identifier map to be absent")
    nodes = {node.ref: node for node in topology}
    from_topology = {nodes[row.edge].fields["node_id"] for row in plan.incidence}
    from_partition = {node.fields["node_id"] for node in partition.nodes if node.kind == 16}
    if len(from_topology) != len(plan.incidence) or from_topology != from_partition:
        raise ValueError("the generated partition has a different edge inventory")
    existing_ids = permanent_edge_ids(partition)
    face_ids = dict(plan.allocation.faces)
    output = {}
    for row in plan.incidence:
        selected = topology_node(nodes, row.positive_fin, 17)
        if selected.fields["edge"] != row.edge or selected.fields["sense"] != "+":
            raise ValueError("boundary roles require the actual oriented edge incidence")
        extra = []
        for key, relation in ((2, "backward"), (3, "forward")):
            neighbor = topology_node(nodes, selected.fields[relation], 17)
            edge = topology_node(nodes, neighbor.fields["edge"], 16)
            if edge.fields["node_id"] in existing_ids:
                raise ValueError("a boundary edge has a permanent identifier representation")
            partner = topology_node(nodes, neighbor.fields["other"], 17)
            loop = topology_node(nodes, partner.fields["loop"], 15)
            face = loop.fields["face"]
            if face not in face_ids:
                raise ValueError("boundary fallback requires the actual allocated face")
            extra.append((key, face_ids[face]))
        output[row.edge] = (*row.face_role_ids, *extra)
    return output
