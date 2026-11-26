<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Worker transport fixture reservations

The builder worker transport fixture creates a real controller and supervisor
configuration. Inheriting the production memory reserve can leave its deliberately
blocked jobs queued before their first attempt. On the observed host, about
4.17 GiB was available; the 4 GiB production reserve left less than the 256 MiB
inference or 2 GiB native worker admission requirement.

The fixture selects zero reserved CPUs and zero reserved memory in its own
`Supervisor.json`. Worker memory limits, application resource capacity, assertions
and production reservations remain unchanged. Both fixture modes reject before
any model or native application call. The host must still have enough available
memory for each worker's unchanged admission requirement.

See the [fixture resource correction](../../../../Changes/Research/Supervisor/Catalogue/WorkerTransportFixtureResources.md).
