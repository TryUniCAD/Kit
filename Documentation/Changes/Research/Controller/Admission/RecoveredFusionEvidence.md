<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Recovered Fusion supplemental admission

## Behavior

A06b needs independently recorded source observations before paired semantic qualification.
The original Fusion handoff was retained locally but absent from the public PR ancestry.
The public preflight previously parked every Fusion lane, including a valid retained source handoff.

The preflight now supports an explicit Fusion raw-chain replay record.
It integrates `FusionRunEvidence.py` and `FusionRunReadbacks.py` from the original source handoff.
`FusionSupplement.py` binds that verifier to the current preflight.
The original source graph supplies capture provenance; the current checkout supplies the candidate native archive roster.
Neither graph is rewritten or merged into the other.

The [manifest guide](../PairedEvidenceManifest.md) defines the fields and command.
Legacy handoff-only records retain their existing behavior.
Missing private inputs remain `waiting_private_evidence`.
Normalized JSON cannot substitute for the raw receipt chain.
Changed source, report, archive, control, or recipe pins refuse admission.

## Recovered evidence

The original owner recorded the [combined handoff](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921995314).
The [native capture record](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6917450974) independently records the collector, plan, and measurement seals.
Those original seals were used for the local replay.
The retained files were read without changing their contents.

The recovered verifier replay passed 38 fresh/historical readbacks and four healthy controls on Fusion build `2706.1.17`.
Both phases retained distinct process identities.
Every observed sketch binding resolved.
P04 retained 14 supporting-face observations and 14 Cut-participant observations.
Aggregate loader warnings remain explicitly unobservable.
This replay did not launch a CAD application or produce new native observations.

## Qualification limits

Every preflight retains `qualified_pairs: 0` and `qualification: not_evaluated`.
Historical receipts, capture identities, frozen rules, P02 qualification separation, and P05 holdout remain unchanged.
The original SOLIDWORKS principal/circle raw chains and coordinated sealed manifest still require their owning custody.
Original SOLIDWORKS P04 supplemental admission remains separate.
The complete-input lineage gate remains unchanged.
Later authoring-tool changes still require adjudication under the original sealed source authority.

Full A06b acceptance also requires independent source-to-neutral adjudication for equal, different, and ambiguous native cases.
Geometry agreement cannot mask inferred constraints, missing loop declarations, dimension operand order, or different construction histories.
Synthetic ambiguous graphs do not supply an independently measured native ambiguous pair.
No reader, writer, conversion, or native acceptance flag is promoted.

## Verification

All seven subprocess cases passed using clean private source commits and the actual preflight command.
It covers missing custody, normalized-report substitution, changed verifier pins, missing handoffs, path escape, unknown qualification fields, and inherited Git overrides.
The original native replay passed separately against its recorded Phase B seal.
The integrated private-chain command admitted the Fusion P01 lane and retained the missing SOLIDWORKS evidence dependency.
It exited `2`, with zero qualified pairs and qualification not evaluated.
A same-size fresh-archive substitution was refused through that command.
The original evidence files retained their hashes.

See the [local custody gotcha](../../../../Gotchas/Research/Workers/Custody/LocalFusionHandoffCustody.md) and [owning step register](../../../../Reference/Research/AutomationSteps.md).
