<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Catalogue capture pipeline

Configure a native worker with `--native-config`, `--native-kind`, and `--native-resource`.
Kit combines the native worker pool with the offline decoder pool in one local supervisor.
Both pools share the host memory and CPU budget.

Kit attaches a reviewed capture when its assessment publishes a receipt that requests evidence.
While Kit prepares the handoff, independent offline work can continue.
The controller releases each dependent job only after it accepts the required evidence.
The configured application resource retains capacity one.
Use `--native-ready` when the application owner has prepared its worker.
Without this option, the controller waits for the owner to mark the resource available.
Kit records the native phase IDs or refusal in `NativeHandoffResult.json`.

The current automatic handoff uses the Fusion two body cut route.
Other catalogue entries continue to use their existing decoder routes or report missing evidence.
The pipeline uses a local controller store and workers configured for that host.

See the [catalogue procedure](../../Controller/DeterministicInference.md#run-both-complete-catalogue-inventories).
