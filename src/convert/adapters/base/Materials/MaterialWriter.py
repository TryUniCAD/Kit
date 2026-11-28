from typing import Protocol, runtime_checkable as RuntimeCheck

from interchange.document.Models.DocumentModel import CadDocument


# the material writer contract needs a dedicated boundary so format boundaries expose consistent document behavior
@RuntimeCheck
class MaterialWriter(Protocol):

    # typed materials needs an explicit validity boundary so format boundaries expose consistent document behavior
    @property
    def TypedMaterials(self) -> bool:
        raise TypeError("a writer must explicitly implement typed material support")


# a writer can restrict typed material publication to its qualified document profiles
@RuntimeCheck
class MaterialScope(Protocol):

    # material scope must be checked before staging and ordinary destination selection
    def SupportsMatDoc(self, DocumentValue: CadDocument) -> bool:
        raise TypeError("scoped material writers must declare their document support")
