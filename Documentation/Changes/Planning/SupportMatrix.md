# Consolidate supported-format and route evidence

## Behavior

B01 now has a revision-bound matrix across all nine roadmap families.
It separates file types, observed versions, read/write boundaries and directional route qualification.
Unsupported endpoints and unknown vendor-version ranges remain explicit.
Existing planner catalogues, corpus coverage and automation registers remain the source inventories.
No planner service, runtime capability API or format implementation is added.

## Usage

Read the [support matrix](../../Reference/Operations/SupportMatrix.md) before selecting or claiming a conversion route.
Use its linked contracts for bounded profiles and measurement requirements.
Use the [backlog](../../Maintenance/ConversionBacklog.md) for ownership and dependencies.

## Coordination and limits

PR #368 retains the SOLIDWORKS census scope.
This matrix links that work without copying its proposed counts or declaring it merged.
Historical NX, CATIA and Creo PR states were refreshed before recording production gaps.
B01 remains checking; unresolved vendor-version promises and full release coverage remain open.
B02–B05 and B12 native qualification requirements are unchanged.

## Verification

Source inspection used main `1619f00bf532caad262d1557bd69281179e5c497`.
Remote PR metadata was read on 2026-11-27.
No CAD, SDK, decoder, test, rendered-document or representative-user execution is claimed.
Formatting and relative-link inspection are recorded in the delivery PR.
Current-head CI and configured review remain separate publication requirements.
