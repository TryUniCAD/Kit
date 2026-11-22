from convert.adapters.solidworks.Container.Format import KInfoValue
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan


# an authored archive name must retain actual atom ownership without claiming an absent native kernel body
def ColdNameSource(OutputValue: ColdOutput) -> Provenance:
    AtomValue = OutputValue.AtomValue
    NameValue = RequireNative(AtomValue.FieldsValue.get("f18"), "moNodeName_c")
    SpanValues: list[ProvenanceSpan] = []
    for NodeValue, RoleValue in (
        (AtomValue, "typed-native-output-atom"),
        (NameValue, "typed-native-output-name"),
    ):
        SpanValue = NativeNodeSpan(OutputValue.LinkValue, NodeValue)
        StreamName = SpanValue.get("stream")
        StartValue = NodeValue.StartOffset
        EndValue = NodeValue.EndOffset
        if (
            not isinstance(StreamName, str)
            or StartValue is None
            or EndValue is None
            or StartValue < 0
            or EndValue <= StartValue
        ):
            raise ValueError("cold output name lacks its actual source span")
        SpanValues.append(
            ProvenanceSpan(StreamName, StartValue, EndValue - StartValue, RoleValue)
        )
    return Provenance(
        adapter=KInfoValue.format_id,
        native_id=f"{OutputValue.LinkValue.ConfigName}:atom:{AtomValue.FieldsValue['f140']}",
        spans=tuple(SpanValues),
    )
