from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace as Replace
from functools import partial as Partial

from interchange.document.Models.DocumentModel import CadDocument


# only an inherited legacy value can be replaced by the verified archive state
def ApplyFlags(
    DocValue: CadDocument,
    Before: Mapping[str, Mapping[str, bool]],
    After: Mapping[str, Mapping[str, bool]],
) -> CadDocument:
    from convert.adapters.freecad.Adapter import MappedOuter, NativeDocPair

    PairValue = NativeDocPair(DocValue)
    Digest = PairValue[0].sha256 if PairValue is not None else ""
    OldFlags = Before.get(Digest, {})
    NewFlags = After.get(Digest, {})
    Sketches = tuple(
        (
            Replace(Sketch, suppressed=NewFlags[Sketch.id])
            if (
                OldFlags.get(Sketch.id) is Sketch.suppressed
                and Sketch.id in NewFlags
                and NewFlags[Sketch.id] != Sketch.suppressed
            )
            else Sketch
        )
        for Sketch in DocValue.sketches
    )
    Transform = Partial(ApplyFlags, Before=Before, After=After)
    Assembly = DocValue.assembly
    if Assembly is not None:
        Assembly = Replace(
            Assembly,
            documents=tuple(
                Replace(ItemValue, document=Transform(ItemValue.document))
                for ItemValue in Assembly.documents
            ),
        )
    return Replace(
        DocValue,
        sketches=Sketches,
        assembly=Assembly,
        metadata=MappedOuter(DocValue.metadata, Transform),
    )
