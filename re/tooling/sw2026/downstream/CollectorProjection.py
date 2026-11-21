from downstream.BoundaryRoles import permanent_edge_ids
from downstream.CacheInputs import attached_part_chains, finalized_part_prefix
from downstream.SurfaceIdentities import clone_collected_surface, cylinder_surface_identities


def fresh_cylinder_collector_fields(attachment, allocation, feature_file):
    partition = attachment.projection.partition
    if permanent_edge_ids(partition):
        raise ValueError("collector needs an admitted representation for each permanent edge ID")
    _, faces, _ = attached_part_chains(partition, allocation, attachment.candidate.HeaderValue.FieldsValue["f48"])

    surfaces = cylinder_surface_identities(attachment, feature_file)
    by_face = {surface.node_id: surface.representation for surface in surfaces}
    members = [{"object": clone_collected_surface(by_face[face.fields["node_id"]])} for face in faces]
    name, high, low = allocation.archive_owner_fields
    return finalized_part_prefix(attachment.candidate, allocation.next_id) | {
        "f30": name, "f38_high": high, "f38_low": low, "f40": members,
    }
