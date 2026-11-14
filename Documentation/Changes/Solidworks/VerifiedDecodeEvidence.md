<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Verified SOLIDWORKS decode evidence

This change publishes [20 controlled decode cases](../../../re/solidworks/measurements/VerifiedDecodeEvidence/README.md) as inspectable neutral model records under `re/`. It includes blind rectangle, pocket, circle, and ellipse cases; two-length and midplane extrusions; and an isolated boss with two cap-edge fillets.

Open a family page and read its fenced JSON to inspect the decoded sketches, constraints, feature links, and driving parameters. The source, reference archive, and model digests identify each observation. The records are research data; production code does not load them. No CAD samples, native archive members, executable writer code, or runtime behavior changes are included.

The historical evidence compares offline-decoded models with independently measured source and target behavior. The application checks measured rebuilt geometry and driving edits. The offline refresh compared full decoded models and native target archives to application-accepted references, then replayed the generated Python with vendor source access revoked. These checks describe the recorded cases and historical build only. The current [SOLIDWORKS adapter](../../Reference/Adapters/Solidworks.md) remains read-only; the entries do not establish broader or strict lossless translation coverage.
