from convert.adapters.solidworks.Container.Format import KInfoValue
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan


# a folder span cannot stand in for the actual named atom and active kernel body
def BodyNameSource(GraphValue: BodyNameGraph) -> Provenance:
    AtomValue = GraphValue.AtomValue
    if (
        AtomValue.StartOffset is None
        or AtomValue.EndOffset is None
        or AtomValue.StartOffset < 0
        or AtomValue.EndOffset <= AtomValue.StartOffset
    ):
        raise ValueError("named body has no actual archive atom source span")
    return Provenance(
        adapter=KInfoValue.format_id,
        native_id=f"{GraphValue.StreamName}:body:{GraphValue.TreeValue.BodyIndex}",
        spans=(
            ProvenanceSpan(
                GraphValue.LinkValue.ConfigName,
                AtomValue.StartOffset,
                AtomValue.EndOffset - AtomValue.StartOffset,
                "typed-native-body-atom",
            ),
            ProvenanceSpan(
                GraphValue.StreamName,
                0,
                GraphValue.StreamLength,
                "native-body-partition",
            ),
        ),
    )
