from dataclasses import dataclass as DataClass


# view support names are explicit authored presentation for five independently owned native feature nodes
@DataClass(frozen=True, slots=True)
class ViewNames:
    DetailName: str
    SheetPlane: str
    SheetProfile: str
    ModelPlane: str
    ModelProfile: str
