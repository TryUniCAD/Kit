<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Retain the pending native readback stage

Task A08f now records native progress before and after application attachment, document opening, control measurement, capture observation and owned exit.
The collector flushes each event to `readback/native-progress.jsonl` before continuing.
Each event carries the configured source revision, exact request hash and directly launched process identity.
Sequence numbers and the preceding event digest bind the complete event chain.
The journal permits at most 1,024 events, 16 KiB per event and 1 MiB overall.

The accepted measurements embed the exact journal text, its digest and its event count.
The listener checks that the embedded text matches its retained journal.
The dispatcher independently verifies the chain, request, process identity, completed stages and final observed disposition.
The existing output-role roster also carries this evidence through the durable measurements artifact.
Historical low-level evidence reads preserve their existing behavior when no journal was recorded.

After a collector timeout or failure, the worker retains the journal digest, last event and pending stage stack with native recovery evidence.
A missing or invalid journal is explicit in that record.
Journal failure cannot prevent the existing exact-handle native cleanup.
Progress recording errors prevent acceptance of a successful current queued run.

The launcher pins the new progress collector alongside both existing collectors.
The circular and principal evidence verifiers record this additional source when present.
Principal verification preserves the historical source bundles and admits the explicitly reviewed instrumented bundle separately.

## Verification

All three C# collector sources compiled against the registered `34.4.1.1011` interop assemblies without an application launch.
The existing rectangular Boss witness also passed its `RunBossWitness.ps1 -CompileOnly` entry point with the added source dependency.
Thirteen native Windows process cases passed with the managed journal writer, Python queue host and actual dispatcher.
They include chain, request-binding, stage-order and incomplete-tail refusals, plus all three safety-helper drift checks with Git replacements.
These cases use disposable processes and fixture observations.

The preceding native P02 attempt used source `7b33e12b2150f1db70e97d935b96042138a08a5a` and reached its bounded deadline.
It accepted zero native observations and published no control measurements.
Exact-ticket recovery terminated the owned process and observed its exit.
All 3,758 recorded source and input hashes were unchanged.
The controller receipt is `059f8a80bd726cf6b9ff1163ed77bdae868f0796b103d4f859fe64e3ef017bd5`.
The recovery record is `ed4c20b24339545e46326408ce7fea49305508b708f898014cafd89da74400d5`.
The new trace must locate the pending call before an evidence-based repair or further native acceptance claim.
No education or license warning was observed through the available application windows during that attempt.
