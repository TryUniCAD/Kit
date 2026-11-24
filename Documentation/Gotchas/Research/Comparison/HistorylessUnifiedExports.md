<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Graph equality does not supply feature history

## Expectation

A unified export retains editable feature history.
Equal parameter values alone cannot supply that history.

## Observed behavior

PR #275 originally copied equal parameter-only documents into `unified/`.
The codec accepts those documents, but conversion preflight refuses them with `MissingFeatureHistory`.
Observed graph equality did not enforce this separate history requirement.

## Resolution

Unified publication checks feature history on both inputs and their embedded documents.
The check uses the same history guard as conversion preflight.
Each document also needs a design body and an active generating history accepted by the SDK feature preflight.
The feature preflight checks typed definitions, dependencies, profiles, suppression, and each body's final generating feature.
Datum-only histories and inactive body generators receive explicit exclusions even when their observed graphs agree.
Excluded inputs retain their reports, input hashes, and graph comparison status.
Read each report or summary row's `unified_exclusions` for the per-side diagnostic.

Installed-command regression coverage compares independently written parameter-only exports.
Equal inputs return exit `0`, retain detailed reports, and produce zero unified copies.
Documents with history retain the existing publication path.
The positive copy fixture now uses the supported reference-sketch and distance-extrusion history contract.
Separate equal-input cases exclude datum-only histories and suppressed body generators while retaining exit `0`.
Additional installed-command cases retain history at both roots and remove history from one embedded document.
The report identifies only the affected input side, checking left and right independently.
Assembly comparison remains unresolved in these cases; its existing status and exit code remain unchanged.
Neither equality nor this history check establishes geometry qualification or native application acceptance.
