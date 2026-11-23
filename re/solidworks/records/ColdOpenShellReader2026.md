# Fresh SOLIDWORKS 2026 inward open-shell readback

The [#121](https://github.com/TryUniCAD/Kit/pull/121) takeover owns this
strict SDK reader slice on `codex/solidworks-121-cold-shell-port`. It ports
the bounded [#262](https://github.com/TryUniCAD/Kit/pull/262) read path to
aggregate base `0bcfe89aa42771224ea01eb4663c1ed11fc7fad7` without its older
chamfer ancestry. The SDK reuses the aggregate configuration links,
saved rollback verifier, edge and face references, retired line and
region decoders, rectangle validation and complete part emitters.
The saved authority comes from
[the #255 record](https://github.com/TryUniCAD/Kit/blob/15749182cdb3142fcab0fbe9719bea21d4a44ee7/re/solidworks/records/SavedOpenShellReader2026.md).
The reader exit condition is guarded SDK readback with unchanged stock
and saved controls. Native generation has separate lifecycle and
held-out exit conditions.

The cold branch requires the ordinary cache-free inventory, one
`Default` configuration descriptor shared by CMgr `f360`, `f368` and the
unique `f370` row, and no saved `f450` association or activation marker.
The actual stock output and shell's `f538` alias the sole Config-0 atom.
The atom retains both feature identities with zero saved body stamps.
The stock and shell carry fresh body states without partition marks.

The stock is a free four-line local Front rectangle with a positive
forward blind driver. The shell's `f828` selects the earlier terminal
cap. Its four side references and the ordered `f848` auxiliary
reference resolve the real sketch segments, common file and stock
creation event. The auxiliary reference contributes no second removal.
The thickness comes from the independent `ThreeDRadiusDim_c.f28` live
parameter and matches the linked display value. The twenty ordered
public feature roots come from the typed graph. The fresh sketch
retains its actual unconstrained state.

The stock prism and inset cavity share the proved stock bounds and
wall thickness. The outer terminal cap takes the reversed cavity loop
as its inner rim. The inner floor and walls reverse their face uses.
The reader checks the resulting boundary, signed volume, surface area
and centroid against the inward offset. Full reads bind the result to
the actual design body without a fabricated native payload or kernel
identity. Design-only mode retains the same drivers, cap, feature
ordering and measured summary.

| Guarded case | File bytes | Stock and shell D1, mm | Volume, mm³ | Area, mm² | Centre Z, mm |
| --- | ---: | --- | ---: | ---: | ---: |
| Calibration | 8,885 | 28 and 2.8 | 18,559.408 | 13,783.12 | 10.810327743 |
| Translated | 8,919 | 36 and 4.15 | 34,018.7535 | 17,224.58 | 14.901582932 |
| Distinct | 8,914 | 23 and 1.875 | 14,392.1484375 | 15,775.375 | 7.852969046 |
| Independent synthetic neutral | 8,949 | 33.25 and 3.1 | 28,355.824 | 18,971.43 | 12.843963607 |

The [guarded process proof](../../tooling/sw2026/shell_source/CheckColdShellRead.py)
rebuilds each neutral request in memory. It checks all three disclosed
whole archives against the [prior typed owner receipt](../measurements/2026/GeneratedOpenShellOwners01.json)
and independently repeats the synthetic request. Both strict modes and
direct inspection JSON round trips pass. Nine transient contrasts each
refuse in both strict modes and stay native-only in permissive
inspection. The guarded workers have zero runtime data reads and launch
no CAD processes. Both direct and public registry publication refuse
without writing to their sinks. The [shared queue integration](../../../tests/Convert/Solidworks/Partition/ShellCacheTests.py)
uses the independent synthetic case.

The crossed-contour contrast exchanges only the last two corner
positions and retains the original line handles and cap owners. The
original #262 reader returned its rectangular 11-face B-rep in both
strict modes despite the crossed sketch. The aggregate's shared
`MakePrismLines` rejects the diagonal sides in both strict modes. The same
process calls `write_document` for `interchange.json` and verifies its
native-history refusal and an untouched sink. Direct inspection JSON
keeps the native-only system rows and is a distinct round trip.

```sh
python3.14 -I -B re/tooling/sw2026/shell_source/CheckColdShellRead.py \
  --generated /path/to/disclosed-generated-archives --output /tmp/KitColdShellRead.json
python3.14 -I -B re/tooling/sw2026/shell_source/CheckColdShellRead.py --model
```

Both saved shell case reports match the
[earlier saved proof](https://github.com/TryUniCAD/Kit/blob/15749182cdb3142fcab0fbe9719bea21d4a44ee7/re/solidworks/measurements/2026/SdkSavedOpenShellRead02.json),
including the crossed active and rollback refusal. The ordinary L1
control retains the aggregate base's exact strict inspection JSON.
The two-stock control exercises four saved part states, its design-only
route and five malformed ownership contrasts. All four disclosed warm
chamfers retain their exact strict inspection JSON and payload hashes
through a fresh-process comparison with the aggregate base. The earlier
chamfer harness expected an empty diagnostics array and refused the
existing informational part-properties diagnostic. The before-and-after
comparison confirms the same diagnostic in both source revisions.
The generated shell files still require native lifecycle and
independent held-out qualification.
[Aggregate SDK proof](../measurements/2026/SdkAggregateColdOpenShellRead01.json)

## Exact source compilation

Task `B04-SW2026-OPEN-SHELL/source-compilation`, owner `/root/format_proofs`, delivery #121, base `ed3243fa745d6ffd8379126db483179a547eb4cd`. The shared `BuildShellPart` constructor accepts the complete strict readback of a generated cold shell in either inspection mode. The construction projection resolves the stock's actual sketch carrier, the selected stock cap and two distinct driving parameter identities. The common cold sketch and boss delegates retain the exact binary metre words. The shell's independent `f818` parameter uses the same inverse, preserving the linked live wall thickness. The fixed stock binding and the older authored neutral constructor use the same stream writers and allocations.

The projection keeps its construction copy separate from the original source. The actual shell creator supplies the temporary body label. The original body name, complete history, attributes, provenance, boundary when requested and retained archive identity all undergo the final strict equality check. The compiler takes the logical locator and creation event from the explicit write inputs. It constructs bytes from the typed model and archive rules before the whole-source comparison.

Three previously pinned generated requests and the independent synthetic request reproduced all four whole archives across full and design-only reads and their inspection JSON round trips. There were 16 exact compilations and 160 logical stream comparisons. The 56 construction refusals covered foreign sketch ownership, the wrong cap, changed wall values, changed body and metadata, and a changed event or locator. The 16 public readback write refusals left the output stream untouched. Both strict read modes of each actual disclosed saved shell still read their live dimensions and body geometry and refuse cold compilation. [Guarded receipt](../measurements/2026/SdkColdShellCompile01.json) · [Body label gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Inspection/ColdShellBodyLabelIsDerived.md)

```sh
python3.14 -I -B re/tooling/sw2026/shell_source/CheckColdShellRead.py \
  --pinned-models --output /tmp/KitColdShellCompiler.json
python3.14 -I -B re/tooling/sw2026/shell_source/CheckSavedShellRead.py \
  --disclosure /path/to/Disclosure --check-cold-compiler --output /tmp/KitSavedShellCompiler.json
```

The fresh model proof uses the established generated-archive measurements as digests. The ordinary research command for pre-existing CAD corpus files does not generate these model-only candidates or exercise the internal compiler. The source acquisition receipt at `84d925a36c79c2b3124aba3ac06830c95297bca1` has SHA-256 `d469a4d75549f1c95948047264c118adadb3b843b3376218140baa61c752987b` and precedes the initial constructor `52646d90ab8914e2f8548d5635d97ddd15b8dea3`. It supplies three native-authored source lifecycles, including two independently sealed cases. Written candidates still need native opening, rebuilding, edit and reopen measurements and a paired evaluation against those locked sources. The frozen calibration packet binds `84cc9032447eefd717f9fb4bc3a6c62ecf941af80aa45da861ca7bd1d456f4a1` and awaits a native terminal result.

The saved proof's independent L1 strict JSON control has SHA-256 `28c302ed8a2bed48909484471733b1b4bd59bc49462f24b1bc003bdfba27d0d6` on both the exact aggregate base and this candidate. The original saved-reader proof retains its own earlier control pin. All seven guarded workers recorded zero runtime reads and no CAD process launches. The combined receipt SHA-256 is `6d37583aff89d01d5ce50c580b34ad26e7cd039b1b2ff44fadf110f30a68553b`.
