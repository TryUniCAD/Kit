# Measured cold part conversion through the ordinary CLI

`kit convert SOURCE.SLDPRT TARGET.SLDPRT --native-measurement RECEIPT --json` now delegates bounded cold-read parts to the same exact writer qualification as the SDK. The previous generic CLI guard rejected source-native origin/history records and retained source metadata before the writer could validate them.

The exception requires the actual registered SOLIDWORKS part writer and its typed cold-reader identity. The writer independently regenerates the part from its neutral profile and driver, compares the complete cold-read document with that regeneration and matches the exact emitted archive to the caller's existing native measurement. It does not use retained source bytes as writer input. Missing or stale measurements and nonmatching source semantics refuse publication without replacing a destination. Other writers retain the generic opaque-record guards.

The complete 79-case archive/process run passes, including two independently measured polygon controls through SDK and fresh-process ordinary CLI conversion with exact equal output hashes and unchanged acceptance reports. Fourteen negative process cases preserve forged-source, extra-feature, opaque metadata, assembly and other-writer refusals. The shared suite includes the process cases and receipt refusals on the existing Windows platform roster. No new CAD call or native measurement is performed by these checks. Reversed candidate publication, broader source families and full decoded-feature support remain unfinished.

The owning child is `A12-ColdCliParity20261127` in the [automation register](../../../Reference/Research/AutomationSteps.md#a12-coldcliparity20261127). The [research inventory](../../../../re/solidworks/DecodedPromotion20261127/Inventory.md) preserves the original two SDK successes and CLI refusals.

The [exact archive/process proof](../../../../re/solidworks/DecodedPromotion20261127/ColdCliParity/README.md) retains both source/output hashes, actual public reports, existing measurements, failed fixtures and verification receipts.
