<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Catalogue pause test synchronization

The catalogue resume integration holds its first supervisor at the first
accepted settlement. The test then runs the ordinary pause command. Its
published marker releases the supervisor to observe the pause before admitting
more work. The test checks for new admissions from the first accepted settlement
through the end of the initial supervisor log, including the interval before
the pause acknowledgement. Resume still uses the ordinary command and verifies
that it preserves the original receipts and completes additional jobs.

The startup hook applies only to the initial test supervisor and the private
catalogue directory. The production scheduler and command interface retain
their existing behavior. The fixture runs through the existing merge-queue
test suite.

[Command guide](../../../../Tasks/ResearchCommandLine.md#run-a-cad-catalogue-with-optional-advice) ·
[Queue failure and cause](../../../../Gotchas/Research/Supervisor/CataloguePauseNeedsPendingWork.md)
