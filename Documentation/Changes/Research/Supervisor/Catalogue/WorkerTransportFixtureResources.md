<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Worker transport fixture resources

`WorkerProbe.py` now explicitly selects zero reserved CPUs and memory in the
supervisor configuration that it creates for its process fixture. This allows
the generation and native rejection probes to reach their intended real worker
boundaries when the host has enough memory for the worker but not an additional
production reserve.

The two `CheckWorker` cases retain their assertions, worker memory limits and
application resource gate. They check typed controller/supervisor/worker input
transport and deliberate capability rejection; neither mode starts a model or
licensed application. Production configuration and resource-policy tests retain
their existing reservations and gates.

The [reservation gotcha](../../../../Gotchas/Research/Workers/Inference/FixtureWorkerReservations.md)
records the observed queued state and its fixture-specific correction.
