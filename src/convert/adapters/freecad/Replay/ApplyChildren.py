from __future__ import annotations

from dataclasses import replace as Replace
from functools import partial as Partial

from interchange.document.Models.DocumentModel import CadDocument


# outgoing child models match the native and historical parses through their own references
def ApplyChildren(
    DocValue: CadDocument, Before: CadDocument, After: CadDocument
) -> CadDocument:
    from convert.adapters.freecad.Adapter import MappedOuter, NativeOuter
    from convert.adapters.freecad.Replay.ApplyFlags import ApplyFlags

    OldOuters = dict(NativeOuter(Before))
    NewOuters = dict(NativeOuter(After))
    Metadata = MappedOuter(
        DocValue.metadata,
        ByReference={
            NameValue: Partial(
                ApplyFlags, Before=OldOuters[NameValue], After=NewOuters[NameValue]
            )
            for NameValue in OldOuters.keys() & NewOuters.keys()
        },
    )
    Assembly = DocValue.assembly
    if Assembly is None or Before.assembly is None or After.assembly is None:
        return Replace(DocValue, metadata=Metadata)
    OldDocs = {
        ItemValue.id: ItemValue.document for ItemValue in Before.assembly.documents
    }
    NewDocs = {
        ItemValue.id: ItemValue.document for ItemValue in After.assembly.documents
    }
    Children = tuple(
        (
            Replace(
                ItemValue,
                document=ApplyFlags(
                    ItemValue.document, OldDocs[ItemValue.id], NewDocs[ItemValue.id]
                ),
            )
            if ItemValue.id in OldDocs and ItemValue.id in NewDocs
            else ItemValue
        )
        for ItemValue in Assembly.documents
    )
    return Replace(
        DocValue, metadata=Metadata, assembly=Replace(Assembly, documents=Children)
    )
