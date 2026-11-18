from interchange.brep.Topology.BrepModel import BrepModel


# complete binding must account for every region shell and face use of the public solid
def CheckBrepOwners(ModelValue: BrepModel, BodyId: str) -> None:
    if len(ModelValue.bodies) != 1 or ModelValue.wires or ModelValue.pcurves:
        raise ValueError("public brep has an unqualified body representation")
    BodyValue = ModelValue.bodies[0]
    if (
        BodyValue.design_body_id not in ("", BodyId)
        or BodyValue.wire_ids
        or BodyValue.vertex_ids
        or set(BodyValue.region_ids) != {Region.id for Region in ModelValue.regions}
        or len(BodyValue.region_ids) != len(ModelValue.regions)
        or not ModelValue.regions
        or any(not Region.solid for Region in ModelValue.regions)
    ):
        raise ValueError(
            "public brep body has incomplete or conflicting design ownership"
        )
    ShellUseIds = tuple(
        ShellUseId
        for Region in ModelValue.regions
        for ShellUseId in Region.shell_use_ids
    )
    ShellIds = tuple(ShellUse.shell_id for ShellUse in ModelValue.shell_uses)
    FaceUseIds = tuple(
        FaceUseId for Shell in ModelValue.shells for FaceUseId in Shell.face_use_ids
    )
    FaceIds = tuple(FaceUse.face_id for FaceUse in ModelValue.face_uses)
    Inventories = (
        (ShellUseIds, tuple(ShellUse.id for ShellUse in ModelValue.shell_uses)),
        (ShellIds, tuple(Shell.id for Shell in ModelValue.shells)),
        (FaceUseIds, tuple(FaceUse.id for FaceUse in ModelValue.face_uses)),
        (FaceIds, tuple(FaceValue.id for FaceValue in ModelValue.faces)),
    )
    if any(
        len(Owned) != len(AllValues) or set(Owned) != set(AllValues)
        for Owned, AllValues in Inventories
    ):
        raise ValueError("public brep contains unbound or multiply owned topology")
    if any(not Shell.closed for Shell in ModelValue.shells) or ModelValue.validate(
        frozenset((BodyId,))
    ):
        raise ValueError("public brep is not a validated closed solid")
