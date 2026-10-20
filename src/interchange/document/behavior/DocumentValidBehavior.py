# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


# document validation methods preserve the historical model surface without owning rules
class DocumentValid:
    locals()["__slots__"] = ()

    # validation remains a model method while independent rules stay in focused modules
    def GetErrors(SelfValue) -> tuple[str, ...]:
        from interchange.document.validation.DocumentValidate import GetDocErrors

        return GetDocErrors(SelfValue)

    # explicit assertion gives model callers the established aggregate exception behavior
    def AssertValid(SelfValue) -> None:
        from interchange.document.validation.DocumentValidate import AssertValid

        AssertValid(SelfValue)
