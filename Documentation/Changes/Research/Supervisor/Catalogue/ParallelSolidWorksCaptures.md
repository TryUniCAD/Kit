<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Parallel SOLIDWORKS catalogue captures

New SOLIDWORKS authoring runs allow up to five native workers on the same
licensed Windows desktop. Set `capture_workers` to an integer from 1 to 5 in
the JSON passed through `--solidworks-host` to lower the cap. This setting is
independent of `--workers`, which controls offline decoding. Kit pins the native
worker count and group identifier with the run. Use a new run directory to
change this setting. Older runs retain their recorded settings.

When **Input dimension value** is enabled in **System Options → General**, Kit
holds the exclusive phase lock while it suppresses and restores the prompt.
When the prompt is already disabled, Kit can run phases concurrently without
writing the preference. The worker checks this setting on its own instance
before allowing overlap. The native startup wait budget accounts for other
configured workers that may need the exclusive lock.

The supervisor increases native concurrency as CPU and memory allow. Five is
the configured cap. The default 4 GiB host reserve, current available memory,
and measured or estimated worker memory can reduce the active count.
Each authoring and reopen phase launches its own process and attaches through
that PID's COM registration. The Windows launcher requires a live same-run
lease for every other SOLIDWORKS process it sees. An unrelated session or
another catalogue cannot join. The shared startup mutex still serializes launch
decisions with existing exclusive tools. Cleanup and process-exit observations
apply to the exact process that the phase started. Native owner receipts include
whether the phase was eligible for overlap and the PIDs of same-run peers observed at startup.

Each case keeps its existing before and after controls, fresh reopen and
separate output files. Verification continues comparing each native file to its
save-time hash. Offline decode still waits for the corresponding accepted
capture.

On Windows at `f5318eb1313de0e0309ec1b8f4b1f2ca92a4118c`, all four process
checks passed in 71.62 seconds. The lease probe accepted the same-run process
and refused foreign and released leases. Catalogue runs verified the
five-worker default, one- and two-worker overrides, the native timeout budget,
and the saved settings after resume. The launcher compiled against the
installed SOLIDWORKS API with the five-worker limit and 20-minute startup wait
budget without starting the application. Licensed overlap, independent normal
exits and archive verification are tracked under
[A08h-ParallelSolidWorks](../../../../Reference/Research/AutomationSteps.md#a08h-parallelsolidworks-same-host-catalogue-capture).
