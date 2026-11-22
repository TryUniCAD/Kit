# Model-only ordinary edge fillet candidates

Task `B04-SW2026-EDGE-FILLET-SOURCES` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The private compiler builds two disclosed one-stock, one-edge, constant-radius
parts for a controlled SOLIDWORKS 2026 SP05.2 trial. The normal writer and the
ordinary and saved readers retain their existing admission conditions.

## Construction rules

The [disclosed modeling intent](../../tooling/sw2026/edge_fillet_source/DisclosedFilletInputs.json)
supplies the two translated rectangular blind stocks, corner incident sides and
live radius. The compiler builds the neutral sketch and boss with the ordinary
part preparation. The shared stock graph binds the actual atom to the boss and
makes the fillet its last modifier. It adds creation events for both owners to
both headers. The ordinary part owners build the configurations, index and
remaining streams. Each full ResolvedFeatures stream is generated with the
actual Config-0 map and one final `Fillet_c` root. No saved stream or partial
native payload enters either compiler.

Each signed face list is computed from actual stock profile order and cap
orientation. The axial case traverses side 2, side 1, end 1, end 0. The
transverse case traverses end 1, side 3, side 2, side 4. The prior native-saved
stock inspection independently confirmed the two positive fin orders. Each
historical carrier refers to the actual earlier boss, with the same computed
creation epoch and active self-file owner. The selected component edge and
the separate radius wrapper share one local edge reference. The selected
wrapper records the actual atom row; the radial wrapper uses the unassigned
component slots. [Native stock acquisition](EdgeFilletStockAcquisition2026.md)

The modeled `D1` length owns a `ThreeDRadiusDim_c` and the corresponding
feature handle, radial text and packed binary64 display cache. The initial
factory and edit paths enter `radiusObject_c` from `sldmopartu!0x18026b94d`
and allocate the current `moDisplayRadialDim_c` at `0x18026d0b8`. The
radius constructor receives the actual feature and scalar. Its solid radial
state starts with bit 2 set at `sldmodu!0x4c8c00b3`. The generated display
takes its line and text style from the generated model. The same initial
display construction is shared with existing validated callers. The guarded
chamfer publication proof retained its recorded complete-file hashes for
both distance branches and the signed control. The
disclosed chamfer regression receipt is
`037b791dcd9bcda42ebbc5f552d4fe3d3846645e3399f0bb841bd994798ad42e`.

The current body-group branch is present. The exact serializer consults
environment option `0x4f3` at `sldmopartu!0x180270560` before writing the
group. The inherited `moBodyFeature_c(model)` constructor initializes
the `+0x730` qword at `sldmodu!0x4b76eff6`, so its contained `f734`
starts at zero. No prior solve, saved mark or partition exists. The result
maps, separate typed result keepers and options array are initialized in their
empty states. The native default constructor and the first-solve path supply
these rules. [Initial options](EdgeFilletInitialOptions2026.md) ·
[Result owners](EdgeFilletResultOwners2026.md)

These spans use preferred virtual addresses in the exact modules pinned by
the [result-owner receipt](../measurements/2026/EdgeFilletResultOwnersStatic01.json).
The exclusive end and SHA-256 identify the original PE code intervals.

| Rule | Module | Span | SHA-256 |
| --- | --- | --- | --- |
| Current body-group gate and scalar | sldmopartu | `0x180270553–0x18027058f` | `f12f2ee795986b78c8c7ae4c99dd6c7943f510ba13445283910de1eacdb37af3` |
| Inherited body-field initialization | sldmodu | `0x4b76efef–0x4b76f003` | `177f5751a90d03e01a187ee7272394407c45abbbb7e10be5556998aab86e48e0` |
| Radius and selected edge wrapper | sldmopartu | `0x18026b910–0x18026b9e4` | `d8d9ef656e31bf68061b6aa74369415fcdb4c5916f745af6a2aac87b907492db` |
| Feature owner and parameter name | sldmopartu | `0x18026a42b–0x18026a458` | `e345621d669fe470ff90f262d3fcc8a49c81ba420789ed8b159dc95d28cabfba` |
| Solid radial display initialization | sldmodu | `0x4c8c0040–0x4c8c01f4` | `0afa3c307a8f5c24b7ce4d01a83472c6e3a3bcc4fd9197d9fbcdeac9db4aaa8e` |

## Guarded proof and native boundary

From the committed checkout, use Python 3.14 and a new absolute output
directory outside Kit.

```sh
python3.14 -I -B re/tooling/sw2026/edge_fillet_source/cold/BuildColdFillet.py \
  --revision EXACT_COMPILER_COMMIT \
  --output /absolute/unused/ModelColdCompile
```

The supervisor alone reads the pinned neutral spec and opens output files.
Each compiler receives a neutral request on standard input. Fresh processes
generate both candidates twice, repeat each case at a different input radius,
and refuse an excessive radius and an unmeasured fin orientation. The
private readback consumes the complete physical archive and re-encodes the
typed ResolvedFeatures bytes. It checks the actual model, stock and atom
aliases, shared signed carriers, creation epochs in both headers and
present empty result owners. It also checks default reader refusal, saved
fillet validation refusal, and rejection of trailing typed bytes. An edit
to just the neutral radius changes only ResolvedFeatures and KeyWords. The
separate analytic predictor supplies volume, surface area, centroid and
oriented cylindrical-face expectations for the upcoming native trial.

The [guarded compile receipt](../measurements/2026/EdgeFilletModelColdCompile01.json)
records eight fresh processes on compiler `346aa4093b510aba3ee88004c53d3f6aed73d361`.
Both candidates have ten streams and a ResolvedFeatures map from 89 through
245 over twenty roots. Their respective SHA-256 values are
`6d28864133d0d291317d309a9835d9fabf2717a073b4f7b435f644b520e18acd` and
`2cd7a0bcc61d19a02a295c16f47d13e660f886a9630728671eecd3d8a9e4c5f7`.
The receipt SHA-256 is
`efe553717fcd7ea1323bd58c138a5a9211f4b022870fdd89d3807f987c8ae8dc`.

`Compile.json` binds exact source and SDK identities, compiler inputs, encoded
locators, whole-file and logical-stream hashes, the complete map endpoints,
typed radius and stock ownership, refusals and runtime read counts. The
candidates must be opened at their respective exact locators under
`C:\KitEdgeFilletModelCold01\Candidates`. The supplied predictions and
files contain no reference output from a saved fillet.

The remaining hypothesis is a fresh `moEdgeRef_c.f70=0` with its four
positive signed supports. The native initial resolver can seek the live
edge from incidence before storing its derived kernel tag. A passing
host replay checks the linkage and byte grammar. Only the licensed,
controlled bracket can establish actual native binding, clean rebuild,
the editable radius, and save and reopen. This research path has zero
native candidate acceptance and zero held-out credit.
[Construction boundary](EdgeFilletConstructionBoundary2026.md)
