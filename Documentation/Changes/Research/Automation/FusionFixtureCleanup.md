<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Remove task-owned Fusion admission clones on Windows

The Fusion admission process fixture creates a private Git clone for each source-verification case.
Git writes read-only loose objects on Windows.
The previous fixture completed its assertions, then failed while removing those objects.
At baseline `e976c927afe0fefcd82f3c6f23ca7f852983f563`, all seven cases passed their assertions but produced seven teardown errors.

The fixture now resolves the clone and owning temporary directory before recursive removal.
The resolved target must be the fixture's direct `Checkout` child.
The cleanup refuses a linked root or a target outside that owner.

A bounded error callback retries only a permission failure from file unlinking.
The target must be a read-only, singly linked regular file within the resolved clone.
Linked or reparse-point files, writable files, and unrelated failures retain their errors.
The retry adds the write permission bit and unlinks that owned file once.
It does not suppress errors or change source-repository permissions.
This uses the [Python 3.11 recursive-removal error callback](https://docs.python.org/3.11/library/shutil.html#rmtree-example).

Run the actual admission process cases with the pinned research environment:

```powershell
python -B -m pytest -q tests/Research/Archives/FusionAdmission/FusionSupplementTests.py
```

On native Windows with CPython 3.14.6, all seven cases completed without teardown errors in 75.67 seconds after the repair.
Black and steering checks passed for the three edited Python files.
This fixture repair does not change admission criteria, native evidence, original custody, or qualification outcomes.

See the [read-only clone gotcha](../../../Gotchas/Git/ReadonlyCloneCleanup.md).
