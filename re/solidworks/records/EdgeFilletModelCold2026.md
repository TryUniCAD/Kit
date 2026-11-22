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
