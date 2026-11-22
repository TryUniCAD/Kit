# Measured Standard sweep writer extracted onto accepted main

The production boundary is the standalone neutral-to-SOLIDWORKS write.
The normal SDK and its direct writer reproduce both measured cold parts on
accepted first-writer base `e5294382aad0c04ba26554dfe381fd03daec110a`.
At this writer revision, the default SDK reader returned legacy partial
history for these files. The subsequent reader proof covers both exact
cold files with full and design-only projection.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
[Cold readback evidence](ScopedSweepReadback2026.md)

## Input and generated owners

- A single active Default configuration, one first-creator solid and two
  distinct owned sketch links. The canonical Right section has a full
  origin circle, fixed centre and driving D1 diameter. The canonical
  Front path has a positive quarter arc, fixed start at the origin,
  horizontal and vertical incidence constraints, and driving D1 radius.
  The actual body owns an unassigned, literal Density in kg/m³.
- `PlanSweepPart` verifies the model topology, relations, supports, both
  parameter owners, density and the complete input capability scope.
  The inputs select no guides, twist, thin walls, saved cache, selections,
  opaque metadata or multiple bodies.
- `BuildSweepPart` shares the ordinary headers, base feature, configuration,
  Definition, stream, compressed archive and sketch-owner construction.
  `MakeGhostPair` allocates both modeled Parasolid sheet owners and the
  actual ghost row references. The explicit sweep context emits only the
  current schema-one Section, Path, Notes, arc and radial fields it needs.
  The embedded Section sheet is synthesized from the circle with computed
  transmit and compressed lengths. There is no saved-body or captured-row
  input. Other resolved writer callers keep their original context.
- The measured write takes an in-memory receipt and exactly reproduces the
  encoded locator, archive bytes and length before publication. Volume,
  area, mass and centre of mass in every original, edit and fresh reopen
  must separately agree with its own two active drivers and the modeled
  density. For section radius `r`, path radius `R` and angle `θ = π/2`,
  the result has volume `πr²Rθ`, area `2πr(Rθ+r)` and centroid
  `(x, R−x, 0)` with `x=(R+r²/(4R))/θ`. The relative bound is
  `5e-7`, with an absolute `1e-11 m` guard for the zero transverse
  component. An edit changes exactly one D1 and its saved reopen retains
  both values. The caller authenticates custody of the unsigned report.

## Provenance and verification

The shared constructor and physical wire rules follow `3fcd6c7fc` and
`862a73077`. The earlier `fd8ddb9f0528fc5c45ce309b240b581872b5aa4b`
extraction records independent typed replays for Config-0, ResolvedFeatures
and GhostPartition. This port retains the actual first-writer runtime and
separately checks unchanged full bytes at both original locators.
[Prior measured sweep record](https://github.com/TryUniCAD/Kit/blob/fd8ddb9f0528fc5c45ce309b240b581872b5aa4b/re/solidworks/records/SweepMeasuredPublication2026.md)

The normalized disclosed measurement has SHA-256
`fc098693d77e0e41e5652eed80fe705b528db9cb9f6ac527fb379784087d83d0`.
It binds the native terminal
`380ead8ff07a9337bd0df87d32eb92e49529e0579c15449767a5ee26e53dd512`,
validity on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, twelve distinct
native lifetimes, both successful brackets and 84 paired comparisons
per slot. The actual authored neutral specification has SHA-256
`e62d1d09ac26cc0ae9538a846b0800023441403b5d04ac432a8f6b1da8e71023`.
Both use epoch `1794000000`.
[Normalized native receipt](../measurements/2026/SdkStandardSweepReceipt01.json)
[Authored input values](../../tooling/sw2026/sweep_source/DisclosedSweepInputs.json)

| Case | Length | Whole archive SHA-256 |
| --- | ---: | --- |
| SweepArcNear | 10,528 | `fd2aefd501b6d3eccf6db1ca3ff927bb50eead360ba29ccc42d2e80a2e96b3ed` |
| SweepArcWide | 10,526 | `e5c7565141dac97b7a7c331a9c7317a3a1bfdfc217915319ec91af18e4f8b9da` |

Run the [fresh process proof](../../tooling/sw2026/CheckScopedSweep.py)
from the checkout. Omit the optional disclosed capture path to run the
same process proof using the pinned digest and normalized evidence.

```sh
python3.14 -I -B re/tooling/sw2026/CheckScopedSweep.py \
  --native /path/to/verified/disclosed/SdkSweepColdDisclosed02
```

Each fresh worker creates portable JSON, derives the full archive without
filesystem input access and compares both public stream paths. Supplying
the original disclosed capture compares every physical stream independently
after verifying both vendor-tested candidate hashes and the terminal receipt.
The proof rejects crossed owners, unresolved metadata, a changed model or
locator, missing evidence, occupied output, and fabricated area, volume
and centroid observations before writing. Actual unverified staged
filesystem targets leave no files.
[Scoped parity receipt](../measurements/2026/SdkScopedSweepWriter01.json)

The earlier independently locked research evaluation used writer
`09b77272b02b74a1b4d54413cc185cb602105527` and passed both aliases,
168 paired comparisons and twelve distinct process lifetimes. Its redacted
receipt SHA-256 is
`d8d698670b21f432e0b6fc98a541d96acf706d9037ad871ec6251fe4be851f70`.
This extraction has no new sealed-input run or additional conversion
credit. The native filesystem route requires its exact measured Windows
locator and is not host-verified here. The later reader starts from the
actual two-row ghost Config-0 owner and uses the same section/path schema
to link both editable drivers and reconstruct the analytic solid.
[Prior protected research evidence](https://github.com/TryUniCAD/Kit/blob/fd8ddb9f0528fc5c45ce309b240b581872b5aa4b/re/solidworks/records/OrdinarySweepHeldoutEvaluation2026.md)
