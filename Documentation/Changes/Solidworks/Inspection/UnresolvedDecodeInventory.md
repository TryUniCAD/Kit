# Committed unresolved SOLIDWORKS decode inventory

The SOLIDWORKS reader and writer plan
(`Documentation/Maintenance/SolidworksReaderWriterPlan.md`, added on
[PR #296](https://github.com/TryUniCAD/Kit/pull/296)) asks for unresolved
findings to be grouped by feature, record and failure reason (baseline item 4).
It also cites a November 25 retry run with about 50 unresolved decoding cases
and 12 capture failures.

This change audits what is actually committed. No committed artifact reproduces
the plan's "50 unresolved / 12 capture failures" accounting: the wording exists
only in the plan commit, and no committed summary uses it. The
[inventory](../../../../re/solidworks/UnresolvedDecodes.md) therefore groups the
committed record instead and states that the plan figure has no committed
source.

## What is committed

`re/NativePlacement2026/Offline/` holds per-case decode receipts, each with a
`counts.unresolved` total and an `unresolved` array of `{path, reason}` entries.
The run decoded 183 inputs strictly (111 SOLIDWORKS, 72 Fusion), carrying 8,619
unresolved entries in total. The receipts bind decoder revision `f643a3dd`.

## Groupings

The inventory groups the 8,619 entries by neutral record/field (feature
definition records, B-rep carrier records, sketch entity geometry, reader
diagnostics, and the record-level acceptance statement) and by feature family
(the SOLIDWORKS rectangular blind-boss ladder and the Fusion identity-placement
family). Each group records its count, an example receipt, and the likely next
step.

## Usage

Read [the inventory](../../../../re/solidworks/UnresolvedDecodes.md) for the
per-group counts and the exact commands that produced them. The commands use
`kit decode` and `re/automation/CompareDecoded.py` read-only against committed
artifacts.

## Limits

The committed receipts come from decoder revision `f643a3dd` and the November 23
placement campaign, not a November 25 run. Receipt paths are neutral-model JSON
paths, not raw stream offsets. No native or application acceptance is claimed,
and the retained-byte entries are expected to remain non-portable. The
inventory executes no native application and adds no decoder rule.
