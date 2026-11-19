from convert.adapters.solidworks.Archive.Mates.RequireMates import KPlanarClasses


# the complete concentric profile must remain separate from arbitrary mixed or unsupported mate lists
def CanReadKinds(ClassesValue: tuple[str, ...]) -> bool:
    return ClassesValue == ("moMateConcentric",) or all(
        ClassName in KPlanarClasses for ClassName in ClassesValue
    )
