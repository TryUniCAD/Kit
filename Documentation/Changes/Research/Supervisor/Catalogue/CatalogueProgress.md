<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Catalogue progress on the command line

During a catalogue run, Kit reports active worker processes and job counts.
It also reports jobs waiting for a CAD session, evidence, or CI.
When queued jobs cannot start, it shows the latest supervisor resource or capacity reason.
A separate worker count keeps grouped process counts distinct from their individual jobs.

Progress appears on standard error. The final result on standard output remains JSON.
The saved supervisor log still contains structured events and detailed admission decisions.

See the [command guide](../../../../Tasks/ResearchCommandLine.md#run-a-cad-catalogue-with-optional-advice).
