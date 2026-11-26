from __future__ import annotations

from dataclasses import replace as Replace
import hashlib as Hashlib

from convert.adapters.freecad.Replay.MappedOuter import MappedOuter
from convert.adapters.freecad.Replay.NativeIdentity import IsNative, KReplaySemanticAttr
from interchange.Core.Common import FreezeMapping as FrozenMapping
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentMetadata import GetSemanticMeta as SemanticMeta
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentPayload import (
    GetPayloadIds as SourcePayloadIndexes,
)


# this definition exists because focused behavior needs one stable owner
def SemanticDoc(DocValue: CadDocument) -> CadDocument:
    EnvelopeIndexes = SourcePayloadIndexes(DocValue)
    AsmValue = DocValue.assembly
    if AsmValue is not None:
        AsmValue = Replace(
            AsmValue,
            documents=tuple(
                (
                    Replace(
                        ItemValue,
                        document=SemanticDoc(ItemValue.document),
                    )
                    for ItemValue in AsmValue.documents
                )
            ),
        )
    Payloads = tuple(
        (
            Replace(
                Payload,
                data=None,
                sha256=(
                    Hashlib.sha256(Payload.data).hexdigest()
                    if Payload.data is not None
                    else Payload.sha256
                ),
                attributes=FrozenMapping(
                    {
                        KeyValue: Value
                        for KeyValue, Value in Payload.attributes.items()
                        if KeyValue != KReplaySemanticAttr
                    }
                ),
            )
            for Index, Payload in enumerate(DocValue.brep_payloads)
            if Index not in EnvelopeIndexes and (not IsNative(Payload))
        )
    )
    MetaValue = MappedOuter(DocValue.metadata, SemanticDoc)
    return Replace(
        DocValue,
        source=CadSource("", "", ""),
        brep_payloads=Payloads,
        metadata=SemanticMeta(MetaValue),
        assembly=AsmValue,
    )


# this definition exists because focused behavior needs one stable owner
def SemanticDigest(DocValue: CadDocument) -> str:
    DataValue = SemanticDoc(DocValue).to_json(indent=None).encode("utf-8")
    return Hashlib.sha256(DataValue).hexdigest()
