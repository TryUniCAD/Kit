from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepBody


# decoded connected regions need exhaustive verified memberships before regrouping
def ReadBrepGroups(ModelValue: BrepModel) -> dict[frozenset[str], str]:
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 2
        or ModelValue.bodies[0]
        != BrepBody(
            ModelValue.bodies[0].id,
            tuple(Region.id for Region in ModelValue.regions),
        )
    ):
        raise ValueError("saved stock cache has alternate decoded body grouping")
    ShellUses = {UseValue.id: UseValue.shell_id for UseValue in ModelValue.shell_uses}
    Shells = {Shell.id: Shell for Shell in ModelValue.shells}
    FaceUses = {UseValue.id: UseValue.face_id for UseValue in ModelValue.face_uses}
    Groups: dict[frozenset[str], str] = {}
    for Region in ModelValue.regions:
        if not Region.solid or len(Region.shell_use_ids) != 1:
            raise ValueError("saved stock cache has alternate decoded solid region")
        Shell = Shells[ShellUses[Region.shell_use_ids[0]]]
        FaceIds = frozenset(FaceUses[UseId] for UseId in Shell.face_use_ids)
        if not FaceIds or FaceIds in Groups:
            raise ValueError("saved stock cache has ambiguous decoded face groups")
        Groups[FaceIds] = Region.id
    return Groups
