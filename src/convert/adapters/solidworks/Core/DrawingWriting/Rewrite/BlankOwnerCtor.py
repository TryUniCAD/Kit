from typing import Protocol


# restored semantic owners need an explicit constructor signature without unbounded argument typing
class BlankOwnerCtor(Protocol):

    # known official fields must retain their names when the trusted typed owner is recreated
    def __call__(self, **Fields: object) -> object: ...
