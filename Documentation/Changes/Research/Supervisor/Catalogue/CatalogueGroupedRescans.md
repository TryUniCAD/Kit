<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Group small catalogue rescans

The catalogue runner can group up to four compatible rescans in one worker.
The worker can reuse its loaded decoder. Each file keeps its own result and accepted receipt.
The combined input size must remain below 16 MiB.
The supervisor checks available memory before admitting a group.

The controller allocates separate job claims for each member.
Several workers can run independent groups when memory and CPU are available.
Use `--workers 1` to cap the run at one offline worker process.

See [research supervisor configuration](../../../../Reference/Research/ResearchSupervisor.md).
