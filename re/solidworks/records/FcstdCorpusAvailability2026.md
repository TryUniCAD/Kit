# FCStd corpus availability

PR #121 still needs the original roster of 165 parts and five assemblies. This source availability audit gives zero production conversion credit to either group. The [machine-readable receipt](../measurements/2026/FcstdCorpusAvailability01.json) binds the retained path and hash evidence.

## Historical audit

The August 11 audit counted resolved FCStd paths from the repository root. Its denominator of 165 included the five documented assembly detections, yielding 160 other paths. The checked records lack the per-path report and source hashes. Its documented assembly locators are `.rescratch/out.FCStd`, the FreeCAD 1.1.3 stock `AssemblyExample.FCStd`, and the `V8_engine.FCStd`, `V8_engine/Conrod_2.FCStd`, and `V8_engine/Piston_2.FCStd` examples. The Mac checkout has none of those five paths. The original provenance of `.rescratch/out.FCStd` remains unresolved. [Historical report](https://github.com/TryUniCAD/Kit/blob/2ac05f439476115605ee911cf6eef6fc4221129e/re/solidworks/CorpusCoverage.md) · [Assembly cases from the same run](https://github.com/TryUniCAD/Kit/blob/2ac05f439476115605ee911cf6eef6fc4221129e/re/solidworks/records/AssemblyClosure.md)

## Available evidence

- The authoritative Mac repository's physical `re/` scan included ignored and untracked entries. It observed 6,403 files in the root and 546 subdirectories, with zero FCStd or FCStd1 paths, zero named document members across 1,772 ZIP and five TAR member tables, and zero wrapped ZIP signatures across 70 standalone XZ decoded headers. This scope covers outer archive metadata and selected headers. It skips symlinks and held-out or sealed paths. [Receipt](../measurements/2026/FcstdCorpusAvailability01.json)
- The original PR #121 head and two historical audit snapshots contain zero tracked FCStd files. Nine modern verification controls appear on accepted main. Two earlier snapshots retain the same two AdditiveBox release controls. Eleven distinct Git blobs account for those cases, with no assembly or link classes in their respective `Document.xml` object tables. The AdditiveBox bytes match disclosed aliases `CADMPEG-19` and `CADMPEG-27`. The nine newer files are separate verification controls. [Control provenance](../../FreeCad/Verification/Provenance.md) · [Path and hash rows](../measurements/2026/FcstdCorpusAvailability01.json)
- The alternative inventory contains 171 resolved paths representing 162 content identities. The SDK read two assembly documents. The writer census attempted two assembly destinations and 169 part destinations, with zero generated files and zero accepted conversions at its pinned revision. The 1.1.4 `AssemblyExample.FCStd` comparator has a disclosed hash and no verified match to the original 1.1.3 file. These sources lack authenticated membership in the requested benchmark. [Alternate inventory](../measurements/2026/DisclosedFcstdSourceInventory01.json) · [Neutral read](../measurements/2026/NeutralCorpusRead01.json) · [Writer census](../measurements/2026/PublicFcstdWriterCensus01.json)

## Reproduce the availability receipt

Run the research tool from a checkout containing the pinned Git objects. Substitute the physical Mac checkout's `re/` path and a new scratch destination. The receipt records Git-relative historical paths, hashes and counts. Any new physical candidate paths appear as hashes of their relative names. The audit starts no CAD process and performs no writing or conversion of CAD files.

```sh
python3.14 -I -B re/tooling/sw2026/freecad_census/AuditFcstdAvailability.py \
  . /path/to/Kit/re /tmp/KitFcstdAvailability.json
```

The requested roster remains unresolved pending original source files or a contemporaneous per-source inventory that binds each identity to its provenance and part or assembly role. [Coverage ledger](../CorpusCoverage.md)
