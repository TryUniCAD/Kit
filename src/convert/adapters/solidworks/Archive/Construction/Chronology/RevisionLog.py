from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import (
    RevisionEvent,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# log captions remain authored text while ownership follows an actual constructed node
@DataClass(frozen=True, slots=True)
class RevisionLog:
    OwnerValue: ArchiveNode
    CaptionValue: str
    EventsValue: tuple[RevisionEvent, ...]

    # unknown event collections or detached numeric identities cannot silently become revision owners
    def __post_init__(self) -> None:
        if type(self.OwnerValue) is not ArchiveNode:
            raise ValueError("revision log requires an actual archive owner")
        _ = ReadStyleText(self.CaptionValue, "revision log caption")
        if type(self.EventsValue) is not tuple or any(
            type(EventValue) is not RevisionEvent for EventValue in self.EventsValue
        ):
            raise ValueError("revision log requires ordered typed events")
