from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Assembly.Display.DisplayMember import DisplayMember


# complete display state reads need actual configuration and occurrence owners
@DataClass(frozen=True, slots=True)
class DisplayOwner:
    ConfigObjectId: int
    ConfigId: int
    ConfigName: str
    ModelObjectId: int
    ModelNativeName: str
    ListObjectId: int
    StateObjectId: int
    StateName: str
    MemberValues: tuple[DisplayMember, ...]
