from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.HasBoundExpl import (
    HasBoundExpl,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.HasBoundNotes import (
    HasBoundNotes,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# related keyword rows share one independent linked configuration and resolved graph read
def HasLocalHelpers(
    Archive: SldprtArchive, RowsValue: tuple[NativeFeature, ...]
) -> bool:
    NotesValue = tuple(RowValue for RowValue in RowsValue if RowValue.kind == "Notes")
    ExplodedValue = tuple(
        RowValue for RowValue in RowsValue if RowValue.kind == "Exploded Views"
    )
    if not NotesValue and not ExplodedValue:
        return True
    try:
        LinkValue = ReadNativeLink(Archive, 0)
        return (not NotesValue or HasBoundNotes(LinkValue, NotesValue)) and (
            not ExplodedValue or HasBoundExpl(LinkValue, ExplodedValue)
        )
    except (KeyError, TypeError, ValueError):
        return False
