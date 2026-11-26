from interchange.Records.RecordConfig import Configuration


# effective extent overrides follow the selected configuration towards its ancestors
def GetAxisConfigs(
    Configurations: tuple[Configuration, ...],
) -> tuple[Configuration, ...]:
    Active = tuple(Config for Config in Configurations if Config.active)
    if not Active:
        return ()
    ConfigById = {Config.id: Config for Config in Configurations}
    if len(Active) != 1 or len(ConfigById) != len(Configurations):
        raise ValueError("requires an unambiguous active configuration")
    Chain: list[Configuration] = []
    Visited: set[str] = set()
    Current: Configuration | None = Active[0]
    while Current is not None:
        if Current.id in Visited:
            raise ValueError("active configuration inheritance contains a cycle")
        Chain.append(Current)
        Visited.add(Current.id)
        ParentId = Current.parent_id
        Current = ConfigById.get(ParentId) if ParentId is not None else None
        if ParentId is not None and Current is None:
            raise ValueError("active configuration inheritance has a missing parent")
    return tuple(Chain)
