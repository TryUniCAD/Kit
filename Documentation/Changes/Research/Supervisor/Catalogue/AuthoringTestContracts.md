<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Typed authoring process contracts

Authoring process fixtures now describe their JSON records, compiled cases, native
archive metadata and source pins with explicit contracts. Runtime research imports
use typed callable boundaries rather than adding the excluded research tree to
production type-checker paths. Controller and native-process calls retain their
existing implementations, arguments, ownership and acceptance assertions.

Nested record readers reject invalid object, array and text shapes before typed
callers inspect them. Existing recipe compilation and transport assertions remain
active. Windows registry and process helpers retain their native platform checks.
No checker settings, baselines, ignored errors or explicit `Any` annotations were
added.

Verification uses strict Mypy and Pyright with the CI Python 3.11 and Linux
configuration. Local process checks passed 104 cases with 27 existing Windows
skips; eight supervisor cases require `os.waitid`, absent from the macOS Python
3.11 checker interpreter, and passed on the supported macOS Python 3.14 runtime.
These process checks do not establish licensed native CAD qualification.
