# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib.metadata import distributions

from Records import digest


# shared external environments must retain their observed package versions throughout the window
def RuntimePins():
    Packages = [
        {"name": NameText, "version": Version}
        for NameText, Version in sorted(
            (Entry.metadata["Name"], Entry.version) for Entry in distributions()
        )
    ]
    return {"packages": Packages, "packages_sha256": digest(Packages)}
