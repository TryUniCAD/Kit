<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deferred exports share the audited import boundary

## Expectation

Deferred facade exports preserve startup behavior without adding another production dynamic-import boundary.

## Observed behavior

PR #284 imported `importlib.import_module` inside `convert/LazyExport.py`.
The existing production dependency policy permits that import only inside `convert/adapters/registry/AdapterDiscovery.py`.
Native queue [run 45387083821](https://github.com/TryUniCAD/Kit/actions/runs/45387083821) exposed this violation through `SourcePolicyTests.py::CheckDeps`.

## Resolution

The facade resolves deferred modules through `LoadExportMod` in the existing canonical boundary.
The gateway accepts valid module names within the production packages only.
It rejects external package roots and malformed module-name segments before dynamic import.
The facade imports the gateway only when an export or child package exists.
Missing-name probes such as `hasattr` raise `AttributeError` before the registry package loads.

The gateway delegates to the existing audited plugin import call.
The three original discovery call sites share that call without adding another suppression for deferred exports.
Production-root and module-name validation remains mandatory before a facade can reach it.

The unchanged dependency policy checks the complete production source tree.
A fresh isolated interpreter checks discovery deferral, missing-name probes without registry startup, public object identity, caching, direct facade child-package lookup, and invalid-module rejection.
Runtime import compatibility does not establish native CAD acceptance.
