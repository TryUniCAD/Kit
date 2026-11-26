from __future__ import annotations

from typing import Callable as ValueFactory
from typing import cast as CastValue

# validator hooks bind late because validation rules sit above immutable storage
KValidatorHooks: dict[str, object] = {}


# one binder installs composed validation entries without importing rule modules upward
def BindValidator(HookName: str, HookValue: object) -> None:
    KValidatorHooks[HookName] = HookValue


# late io policy bindings preserve source and file guards without importing the composed model upward
def ValidateIo(SourceValue: object, IsWrite: bool = False) -> None:
    HookValue = KValidatorHooks.get("file_write" if IsWrite else "source_read")
    if not callable(HookValue):
        raise TypeError("document io validation requires composed bindings")
    ValidatorFunc = CastValue(ValueFactory[[object], None], HookValue)
    ValidatorFunc(SourceValue)


# compat protocol marker exempts paired wrappers from naming constraints
class PairProtocol:
    KSlotsValue = ()

    locals()["__slots__"] = KSlotsValue


# document valid keeps the historical surface because callers depend on it directly
class DocumentValid(PairProtocol):
    locals()["__slots__"] = ()

    # validation remains concrete so callers receive the runtime tuple contract directly
    def validate(self) -> tuple[str, ...]:
        HookValue = KValidatorHooks.get("validate")
        if not callable(HookValue):
            raise TypeError("document validation requires composed bindings")
        ValidatorFunc = CastValue(
            ValueFactory[[object], tuple[str, ...]],
            HookValue,
        )
        return ValidatorFunc(self)

    # assertion remains concrete so callers avoid object returning compatibility lookup
    def assert_valid(self) -> None:
        HookValue = KValidatorHooks.get("assert_valid")
        if not callable(HookValue):
            raise TypeError("document validation requires composed bindings")
        ValidatorFunc = CastValue(
            ValueFactory[[object], None],
            HookValue,
        )
        ValidatorFunc(self)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetErrors(self) -> tuple[str, ...]:
        return self.validate()

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def AssertValid(self) -> None:
        self.assert_valid()
