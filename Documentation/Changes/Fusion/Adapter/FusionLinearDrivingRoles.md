<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Saved Fusion linear driving parameter roles

The Fusion document reader now promotes a uniquely bound linear driving dimension's parameter from reference to driving. Promotion follows the existing typed dimension decoder: native class and kind, reciprocal numeric binding, owned ordered operands, measured scalar, and source driving flag must already validate. Distance, horizontal distance, and vertical distance join the existing radius and diameter cases. Parameter values, expressions, owners, identities, provenance, and source bytes remain intact.

Shared parameters, reference dimensions, unsupported kinds, and sketches carrying dimensional decoding diagnostics retain reference roles. Angular roles remain unqualified. No selected-profile loops are manufactured from authored contour geometry. P01's empty declared-loop inventory remains unchanged, and its profile semantics remain an A06b qualification requirement.

Fourteen P01/P03 discovery archives pass native decoding and neutral JSON round trips with all 28 width/height parameters driving. An independent local recheck compares those same sealed archives against the recovered native Phase B after-recompute driving flags and ordered point targets. Five altered native archive controls retain reference roles for reference, shared, unknown-flag, unsupported-kind, and ambiguous-binding cases. Five saved radial/angular controls preserve their previous roles.

These are partial source-inventory corrections. A06b qualification still requires the remaining independent source and native acceptance evidence, including the SOLIDWORKS raw chain and explicit profile-semantics adjudication. P02 qualification and P05 holdout data were not used, and no CAD application was launched.
