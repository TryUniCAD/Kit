from __future__ import annotations

from dataclasses import dataclass as Dataclass
from xml.etree.ElementTree import Element


# archive parsing and parameter binding share the same native object identity and properties
@Dataclass(slots=True)
class NativeObject:
    name: str
    type_id: str
    index: int
    object_id: str
    touched: bool
    dependencies: tuple[str, ...]
    extensions: tuple[Element, ...]
    transient_properties: tuple[Element, ...]
    properties: dict[str, Element]
