from __future__ import annotations

from interchange.document.Models.DocumentModel import CadDocument


# validated source hashes identify each sketch baseline even when child paths change
def ReplayFlags(DocValue: CadDocument) -> dict[str, dict[str, bool]]:
    from convert.adapters.freecad.Adapter import IsPayloadMap, IsPayloadSeq

    Pending = [DocValue]
    SeenDocs: set[int] = set()
    Flags: dict[str, dict[str, bool]] = {}
    while Pending:
        Current = Pending.pop()
        Identity = id(Current)
        if Identity in SeenDocs:
            continue
        SeenDocs.add(Identity)
        Flags[Current.source.sha256] = {
            Sketch.id: Sketch.suppressed for Sketch in Current.sketches
        }
        if Current.assembly is not None:
            Pending.extend(
                ItemValue.document for ItemValue in Current.assembly.documents
            )
        NativeMeta = Current.metadata.get("freecad")
        if IsPayloadMap(NativeMeta):
            External = NativeMeta.get("external_documents")
            if IsPayloadSeq(External):
                Pending.extend(
                    Linked
                    for ItemValue in External
                    if IsPayloadMap(ItemValue)
                    and isinstance((Linked := ItemValue.get("document")), CadDocument)
                )
    return Flags
