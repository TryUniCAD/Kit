<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Pause and resume a catalogue run

Use `kit run --directory DIR --pause` with the same checkout and format selectors as the original run.
Kit stops taking new jobs and allows active workers to finish.
When the previous invocation has exited, use `--resume` with the same output directory.
Kit reuses the submitted jobs, accepted receipts and settings prepared by the first invocation.

Keep the checkout at the original Git revision.
Use `--max-seconds` on resume to change that invocation's time limit.
Use `--native-ready` only after the native owner has prepared the application.
The latest report replaces the previous report. The run logs remain in the same directory and append on resume.

This applies to runs prepared with this version. See the [command guide](../../../../Tasks/ResearchCommandLine.md#run-a-cad-catalogue-with-optional-advice).
