<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Shared SOLIDWORKS COM registration can select another instance

## Expectation

A launcher can start a SOLIDWORKS process and use the registered application
object to automate that process.

## Actual behavior

The class-wide application registration can resolve to an already-running
instance. The catalogue's serial guard made that lookup viable when a fresh
owned process was the only one. Two same-host workers cannot use the same
class-wide lookup to identify their respective launches. Dassault documents
starting each instance separately and finding its COM object by process ID in
the Windows Running Object Table.
[Vendor API guidance](https://3dswym.3dexperience.3ds.com/wiki/solidworks-news-info/getting-started-with-the-solidworks-api-solidpractices_eLpSxUm2THqG6jwQdSrMGQ)

## Workaround

Look up the exact launched process ID from the start in parallel mode. Verify
that the API reports the same ID and that the held process and empty-document
checks pass before issuing application or file operations.
[Parallel catalogue capture](../../../../Changes/Research/Supervisor/Catalogue/ParallelSolidWorksCaptures.md)
