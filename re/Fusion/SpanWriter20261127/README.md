# Generated two-sided circular offset spans

Full SDK/CLI read/write support is unfinished. This is source-free writer research for child `A11-GeneratedOffsetSpan20261127`, not public support or native acceptance.

The parent task `A16-DecodedReadWrite20261127` owns the full decoded SOLIDWORKS/Fusion promotion request on `feat/decoded-cad-read-write-20261127`, from freshly fetched main `91a73de348894a5791a51b977cd6fe0fe677a617`. Existing writer PRs #121/#244/#297/#299/#303 and offset reader #396 retain their separate scopes.

## Implementation and field ownership

`Generate.py` reuses the existing symbolic AuthorState allocator, foundation/sketch/extrusion/material builders, complete Design/ACT/Browser/container emitters and cylindrical BRep/history generator. It creates new object identities and parameter/binding allocation from dimensions, without loading a native source or modifying a captured payload.

The explicit OffsetStart has five separately owned extent controls. AlongDistance links to the firstDistance user parameter; AgainstDistance, ProfileOffset and both zero taper roles have independent reciprocal parameter and feature references. Native lengths are centimeters; public/request lengths are millimeters. Direction type 2, side-2 distance extent type 1 and start type 1 come from the existing typed field vocabulary and [signed-offset evidence](https://github.com/TryUniCAD/Kit/tree/26db5212b15e30bbed41f3c8964bed9490280d41/re/Fusion/OffsetStart20261127). These scalar meanings are known; their complete generated-file coupling is not yet native-qualified.

The generator derives the solid interval `[offset-second, offset+first]`, height, circular geometry, volume, area, centroid and full mass tensor analytically. It emits new history/body records from that cylinder and existing format vocabulary. Feature labels, history/progenitor relationships and native edit survival remain candidate hypotheses until actual target validation; typed equality alone cannot prove them.

`RunLadder.py` exercises 13 parameter combinations, varying radius, first distance, second distance and negative/zero/near-zero/positive placement independently, with two additional combined parameter probes. They are not independent native holdouts. All thirteen generated files pass complete typed parse/emit/parse equality. The construction audit permits only package grammar and interpreter code reads; four repository schema resources and one Python codec import were observed and hashed, with no CAD-source reads. Original runtime paths are private; published resource paths identify the checkout or interpreter module.

`CheckGenerated.py` runs the independently pinned #396 reader at `7ce58d3962f89c5c184e1fd993126e4927f9d73d`. It checks all five actual bound parameter values and owners, mode/start/operation, volume/area/centroid, and the existing independent full analytic mass-cache validator. The ladder passes 104 recorded comparisons and every additional ownership/cache assertion. An initial three-case probe passes 24 comparisons.

The public strict reader still refuses every generated candidate with `Native Fusion state is outside the qualified authored feature profile`. No public write/read guard, qualification metadata or application attestation was changed. Native acceptance flags remain false because no candidate was measured in the target application.

## Reproduction

Use a Python 3.14 environment and the pinned production sources; choose unused output directories:

```sh
PYTHONPATH=/absolute/main91a/src python re/Fusion/SpanWriter20261127/RunLadder.py /absolute/unused/output
PYTHONPATH=/absolute/reader7ce/src python re/Fusion/SpanWriter20261127/CheckGenerated.py /absolute/unused/output
```

The generator does not invoke CAD software or models. Its immutable source digest is bound in the ladder report. `Initial/` and `Ladder/` retain the exact independently generated candidates and reports. `Evidence/FailedAttempts.json` retains comparison, packaging and connectivity failures.

## Remaining work

The tailnet CAD API timed out before any native job submission. A local Tailscale CLI query also could not contact its daemon socket. No native lease was acquired, no application was launched and no other session was disturbed.

Once the existing tailnet transport is reachable, the root-owned exclusive worker must bracket each exact candidate with healthy controls, inspect initial/rebuilt feature and solid state, independently edit first/second/offset drivers and circle geometry, restore, save and reopen each derivative in a fresh process. Retain exact executable build/hash, candidate hashes and all observations. Prove held-out combinations and inconsistent-binding/topology counterexamples before production promotion.

Generated neutral edits, lossless arbitrary source admission, non-XY/translated profiles, drafting, revolves and other feature families remain required under the parent inventory. This research does not establish conversion acceptance or complete the user's request.
