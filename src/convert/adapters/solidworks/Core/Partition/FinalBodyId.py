from interchange import FeatureKind
from interchange import FeatureStep


# this definition exists because focused behavior needs one stable owner
def FinalBodyId(
    Timeline: tuple[FeatureStep, ...], OperationFeatureIds: frozenset[str]
) -> str:
    Choice = next(
        (
            Feature
            for Feature in reversed(Timeline)
            if Feature.id in OperationFeatureIds
            or (
                isinstance(Feature.kind, FeatureKind)
                and Feature.kind != FeatureKind.REFERENCE
                and (Feature.kind != FeatureKind.SURFACE)
                and (Feature.kind != FeatureKind.NATIVE)
            )
        ),
        None,
    )
    if Choice is not None:
        return Choice.id
    return Timeline[-1].id if Timeline else ""
