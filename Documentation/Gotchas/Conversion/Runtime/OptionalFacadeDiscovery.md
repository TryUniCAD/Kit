<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Optional exports can block plugin discovery

## Expectation

An installed plugin can expose usable adapters without its optional user-interface dependencies.
Custom `__dir__` output does not determine which direct adapter classes discovery can find.

## Observed behavior

Resolving every advertised module attribute invoked unrelated lazy exports.
A missing optional dependency then stopped discovery before the available adapter registered.
The [review finding](https://github.com/TryUniCAD/Kit/pull/286#discussion_r4685741051) records this regression.

## Resolution

Inspect the direct module namespace for third-party plugins.
Resolve only declared `KPublicExports` names on the known Fusion and SOLIDWORKS Core facades.
Keep the direct namespace inspection when a plugin hides names through `__dir__`.

The filesystem discovery integration covers hidden names and an optional export that raises `ModuleNotFoundError`.
All four combinations must register the usable JSON adapter through `AdapterRegistry.introspect`.
Deferred facade checks also retain child-package lookup and rejection of external or malformed module names.
