<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Parallel catalogue workers

Kit automatically starts independent offline catalogue jobs when enough memory and CPU are available.
The supervisor adjusts its worker count as resource conditions change.
It uses the memory above the configured reserve and the workers' measured and estimated needs.

Use `--workers N` to set an upper bound on offline workers. Use `--workers 1` to run jobs in series.
The supervisor uses this ceiling for the offline pool. A mixed pipeline shares the controller job capacity.
Each active offline catalogue worker holds one job claim.
The optional native stage uses its supplied worker configuration and CAD application ownership rules.

See the [research command guide](../../../Tasks/ResearchCommandLine.md#run-a-cad-catalogue-with-optional-advice).
