# Committed unresolved decoding findings

This groups the unresolved decoding findings that are actually committed in this
repository. It does not claim to reproduce the plan's Nov 25 figures.

## The plan figure has no committed source

The SOLIDWORKS reader and writer plan
(`Documentation/Maintenance/SolidworksReaderWriterPlan.md`, added on
[PR #296](https://github.com/TryUniCAD/Kit/pull/296)) says:

> The November 25 retry run recorded 50 cases with unresolved decoding and 12 capture failures.

No committed artifact reproduces those figures. The wording exists only in the
plan commit:

```sh
git fetch origin pull/296/head:pr296
git log --all --oneline -S"unresolved decoding"
# d9ab9e067 docs: plan deterministic SOLIDWORKS reader and writer delivery
git log --all --oneline -S"capture failures"
# d9ab9e067 docs: plan deterministic SOLIDWORKS reader and writer delivery
grep -rIl "unresolved" re Documentation
```

No committed summary uses the plan's "50 unresolved / 12 capture failures"
accounting. The number is a plan-author figure whose source run was not
committed. What follows is the closest committed record: per-case decode
receipts that carry an explicit `unresolved` list.

## The committed record

`re/NativePlacement2026/Offline/` is an offline replay of committed native
inputs. Its README records 255 committed-file replays; 183 produced a strict
decode and a `Receipt.json.gz`, and 72 were strictly refused with no receipt.
The decoder revision is `f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2`
(`sdk_revision` in every receipt).

Every receipt has `counts.unresolved` and an `unresolved` array of
`{path, reason}` entries. Those entries are the committed record of unresolved
decoding:

| decode set | source corpus | files | unresolved entries each | entries |
| --- | --- | ---: | ---: | ---: |
| SOLIDWORKS `.SLDPRT` | `re/solidworks/FeatureLadderRecovery/Cases/solidworks-059..095` | 111 | 77 | 8,547 |
| Fusion `.f3d` | `re/FeatureLadders2026/Cases/fusion-000..` | 72 | 1 | 72 |
| total | | 183 | | 8,619 |

Each SOLIDWORKS case contributes three roles (`control-before`, `variation`,
`control-after`). Detection:

```sh
python3 -c '
import json, gzip, glob, os, collections
files = sorted(glob.glob("re/NativePlacement2026/Offline/*/Receipt.json.gz"))
apps = collections.Counter()
tot = 0
for f in files:
    d = json.load(gzip.open(f))
    apps[d["source"]["format"]] += 1
    tot += d["counts"]["unresolved"]
print(len(files), "receipts", dict(apps), "unresolved", tot)
'
# 183 receipts {"sldprt": 111, "f3d": 72} unresolved 8619
```

The public neutral decode does not surface these as a field. The committed
receipt does. On a clean part the neutral JSON carries no `unresolved` text:

```sh
kit decode "re/solidworks/examples/.SLDPRT/example.SLDPRT" -o /tmp/example.json
python3 -c 'import json; s=json.load(open("/tmp/example.json")); print(s["kind"], s["partial"], "unresolved" in json.dumps(s))'
# part False False
```

## Groups by failing record and field

Across the 183 receipts the unresolved entries collapse to a handful of neutral
paths. Counts below are occurrences across all receipts (a SOLIDWORKS case
contributes 77 each; a Fusion case contributes 1).

| neutral record / field | reason | count | cases |
| --- | --- | ---: | ---: |
| `/feature_timeline/*/definition` | `native_only_record` | 2,775 | 111 SOLIDWORKS |
| `/feature_timeline/*/definition` | `direction_frame_operation_require_independent_evidence` | 111 | 111 SOLIDWORKS |
| `/feature_timeline/*/definition/object_data/record_data` | `retained_bytes_are_not_portable_semantics` | 2,775 | 111 SOLIDWORKS |
| `/brep/curves/*/attributes/carrier_record` | `retained_bytes_are_not_portable_semantics` | 1,332 | 111 SOLIDWORKS |
| `/brep/surfaces/*/attributes/carrier_record` | `retained_bytes_are_not_portable_semantics` | 666 | 111 SOLIDWORKS |
| `/brep_payloads/*/data` | `retained_bytes_are_not_portable_semantics` | 333 | 111 SOLIDWORKS |
| *(record level, empty path)* | `independent_source_inventory_and_native_acceptance_unavailable` | 183 | all 183 |
| `/diagnostics/*` | `reader_diagnostic` | 111 | 111 SOLIDWORKS |
| `/metadata/solidworks_source_bytes` | `retained_bytes_are_not_portable_semantics` | 111 | 111 SOLIDWORKS |
| `/sketches/*/entities/*/geometry` | `native_only_record` | 111 | 111 SOLIDWORKS |
| `/sketches/*/entities/*/geometry/data/record_data` | `retained_bytes_are_not_portable_semantics` | 111 | 111 SOLIDWORKS |

Counting command:

```sh
python3 -c '
import json, gzip, glob, collections, re
c = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob("re/NativePlacement2026/Offline/*/Receipt.json.gz")):
    for x in json.load(gzip.open(f))["unresolved"]:
        p = re.sub(r"\d+", "N", x.get("path", "")) or "(record level)"
        c[p][x["reason"]] += 1
for p, r in sorted(c.items(), key=lambda kv: -sum(kv[1].values())):
    print(sum(r.values()), p, dict(r))
'
```

### G1. Feature-definition records (2,886 + 2,775 entries)

The largest group. Every SOLIDWORKS feature-timeline definition body is a
`native_only_record`, and its nested `object_data/record_data` is retained bytes
with no portable semantics. The `direction_frame_operation_require_independent_evidence`
entry is the operation/direction/frame triple that needs an independent source
inventory before it can be claimed.

Example: `re/NativePlacement2026/Offline/offline-001/Receipt.json.gz`
(`re/solidworks/FeatureLadderRecovery/Cases/solidworks-059/control-after.SLDPRT`).
Next step: give the `feature_timeline` definition bodies a typed owner from
loader evidence, and separately source the direction/frame/operation fields from
a held-out authored control.

### G2. B-rep carrier records (1,332 + 666 + 333 entries)

Curve, surface and `brep_payloads` carrier records are retained bytes only.
Next step: a B-rep carrier-typing track; it needs Parasolid-level evidence and
is outside the current sketch/feature reader work.

### G3. Sketch entity geometry (111 + 111 entries)

`/sketches/*/entities/*/geometry` is a native-only record and its
`geometry/data/record_data` is retained bytes. This is the same seam the sketch
sweep tasks target. Next step: decode the sketch entity geometry records
(circles, arcs, relations) against committed ladder sketches.

### G4. Reader diagnostics and source bytes (111 + 111 entries)

One `reader_diagnostic` per SOLIDWORKS case and the retained
`metadata/solidworks_source_bytes` copy. Next step: inspect the diagnostic
reason per case; the source-bytes entry is expected and can never be portable.

### G5. Whole-document acceptance (183 entries)

One record-level entry per receipt:
`independent_source_inventory_and_native_acceptance_unavailable`. This is not a
field failure; it states the run had no independent source inventory or native
acceptance. It covers all 111 SOLIDWORKS and all 72 Fusion receipts. Next step:
pair each committed input with an independently authored and measured control
(the plan's baseline item 5).

## Groups by feature family

| family | corpus | files | cases | unresolved per file |
| --- | --- | ---: | ---: | ---: |
| SOLIDWORKS rectangular blind-boss ladder | `re/solidworks/FeatureLadderRecovery/` | 111 | 37 | 77 |
| Fusion constrained prism / identity placement | `re/FeatureLadders2026/` | 72 | 24 | 1 |

The SOLIDWORKS family uses three principal planes, both extrusion directions and
decimal width/height/depth variations; every one of the 111 roles carries the
same 77-entry structural pattern, so the unresolved set is not feature-specific
within the family. The [package README](../../re/solidworks/FeatureLadderRecovery/README.md)
records that only 15 front-plane files also match the native centroid while all
48 top-plane and 48 right-plane files have incorrect neutral placement.

The Fusion family is the identity-placement refusal class; its single
record-level entry is the same acceptance statement. This matches the separate
refusal recorded in the [placement campaign README](../../re/NativePlacement2026/README.md).

## Cross-check with the comparison tool

`re/automation/CompareDecoded.py` reports per-side issues on committed decoded
documents. Comparing the `control-before` and `variation` documents of one
SOLIDWORKS case:

```sh
mkdir -p /tmp/cmp/left /tmp/cmp/right
gzip -dc re/NativePlacement2026/Offline/offline-002/document.json.gz > /tmp/cmp/left/doc.json
gzip -dc re/NativePlacement2026/Offline/offline-003/document.json.gz > /tmp/cmp/right/doc.json
python3 re/automation/CompareDecoded.py --left /tmp/cmp/left --right /tmp/cmp/right --unit mm -o /tmp/cmp/out
# {"exit_code": 3, "outcomes": {"different": 1}, "pair_count": 1}
```

The run reports `different` with 26 feature correspondences and 370 per-side
issues; the top reasons are `unclassified_native_or_extension_fields` (52),
`native_only_record` (50), `unclassified_reference_semantics` (100),
`retained_bytes_are_not_portable_semantics` (52) and `uninterpreted_native_value`
(42). These are the same seams as G1/G3 and are consistent with, not additional
to, the receipt groups. The comparison is between two different documents, so
`different` is expected; it is used here only for its issue inventory.

## Limits

- The committed receipts are from decoder revision `f643a3dd` and the Nov 23
  placement campaign, not a Nov 25 run. The plan's "50 / 12" figure therefore
  has no committed backing and is not asserted here.
- Receipt `path` values are neutral-model JSON paths, not raw stream offsets.
  Mapping them to exact `Contents/*` streams needs the reader's stream/record
  dispatch, which is not recorded in these receipts.
- No native or application acceptance is claimed. The retained-byte entries are
  expected to remain non-portable by design.
