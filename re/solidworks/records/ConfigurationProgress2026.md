# Configuration progress after generated history construction

Status: the generated marker permits clean native regeneration of the first
prism. Depth editing and the broader locked batch remain pending. Production
writing remains disabled.

## Measured trigger

The [model-appearance measurement](../measurements/2026/FreshPartModelAppearance.json)
opens generated candidate `f3a2169124976ca55524bc83ef6c2f6c5825baea912900b411a9e5bfad8af079`
without open or rebuild errors, but its ordinary sketch and extrusion are
suppressed and no body exists. Both original controls pass. The diagnostic
vendor intervention is separate from generated-output acceptance.

In the [controlled intervention](../v2026/evidence/TupniUnsuppression.json),
the vendor API unsuppresses both features successfully and rebuilds one solid
with the expected triangle-prism volume `9.932000000000002e-6 m³`, zero feature
errors and no warnings. The original control remains healthy and both input
hashes remain unchanged. That changed in-memory model is not a generated-file
success and is never loaded by the writer.

## Native suppression rule

`moBaseConfiguration_c::getSuppressedState(feature)` at `0x4bddae80` can apply
its default state when all of the following hold:

- The configuration has no inherited base configuration.
- The feature is a suppressible concept and has no explicit per-feature object.
- Its native virtual predicate at `+0x1960` is true and the configuration needs a rebuild.
- The feature's persistent ID exceeds configuration member `+0x85c` and is not `0x26`.

That branch returns bit 0 of the default object at configuration `+0x4d0`,
member `+0xc`. Its native constructor's value is one. The ordinary no-object
lookup for an already processed feature returns unsuppressed zero instead.

Both current feature families ultimately use `moFeature_c::isSuppressed` at
`0x4bb4bf50`, normally reading whether feature `f298` equals one. The feature's
constructor-zero `f298` remains correct; changing it is not the recovered fix.

## Derived completed-update marker

The native common update at `0x4bdb3c90` calls `moHeader_c::getHighestID` at
`0x4bdb64fc`, then stores that result in configuration member `+0x85c` at
`0x4bdb6502` and `0x4bdb650d`. The latter is its companion configuration.

The header getter at `0x31a05230` returns `header.f08 - 1`: load the signed
32-bit next-ID counter at `+0x08`, decrement once, return. Thus the formula is
`configuration.f85c = allocator.next_id - 1`, not the next counter itself.
For the current graph, next ID 25 gives highest processed ID 24.

These addresses bind to the 2026 binaries:

| Binary            | Preferred base | SHA-256                                                            |
| ----------------- | -------------- | ------------------------------------------------------------------ |
| `sldmodu.dll`     | `0x4b140000`   | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldarchiveu.dll` | `0x319f0000`   | `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48` |

The shared `record_configuration_progress` operation applies the formula after
the neutral history and live parameters allocate their IDs, before either
configuration stream is serialized. The general constructor's initial zero and
default suppression flag remain unchanged. The marker comes from the generated
graph, never a saved document or a fitted literal.

The complete-file subprocess check independently decodes `Header2` and `CMgr`
and checks that the active configuration's persisted marker equals the header's
next counter minus one. Existing strict construction access denial and linked
archive-map checks remain enabled. Remote job `132815940695` passed the
149 policy process checks and 163 native process checks, with 158 existing
fixture skips, retaining artifact `14162162423` from head
`0212d3ce3b391ebfdaac133a33ed049407c287cd`.

The [new clean measurement](../measurements/2026/FreshPartConfigurationProgress.json)
opens generated H3 SHA-256
`f3318f14461e16d410125aef041e68c293becbbb3a8ddc0cff544cee13d2409a`,
7,070 bytes, and rebuilds one solid without unsuppression or another vendor
intervention. Volume is `9.932000000000002e-6 m³`, area
`0.003166276360558158 m²`, and center is
`(0.006666666666666669, 0.007000000000000002, 0.0065) m`.
Both original controls pass on exact build `34.5.2.0604`; both input hashes
remain unchanged. No open errors, warnings, feature errors, dialogs or cleanup
errors are observed. Depth editing, saved-copy reopening and the remaining
locked family cases are separate unfinished checks.

## Unfinished override persistence

Separate native `Contents/CnfgObjs` persistence calls
`moBaseConfiguration_c::SerializeConfigObjects` at `0x4bdc60e0` for explicit
per-feature/configuration overrides. Its absence is not independently proven to
cause suppression in this single active configuration once the processed marker
covers all current feature IDs. Its grammar and generated override coverage
remain unfinished. No recorded fallback or default-flag workaround is added.
