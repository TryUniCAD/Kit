# Verify a strict JSON cuboid height edit

The [research command](../../../../re/Fusion/SavedCuboidRoundTrip/RegenerateSdkHeightEdit.py)
accepts edited JSON from the public SDK's strict read of the generated
body-scene profile. Change only the independent height driver's
millimetre literal and its neutral value. The tool resolves the driver
through the actual extrusion binding. It generates a fresh native
model with updated solved geometry and strict SDK readback.

```text
python -B re/Fusion/SavedCuboidRoundTrip/RegenerateSdkHeightEdit.py PinnedDependencyCheckout Edited.json NewEvidence --written-at 1795824000
```

Use the same pinned [#337](https://github.com/TryUniCAD/Kit/pull/337)
checkout and epoch used to generate the source. The tool fully
regenerates the original model and verifies its archive digest and
complete projected state before applying the edit. It refuses other
semantic changes, unrecognized metadata, and sources outside that
reproducible scope before creating the output directory. Its process
blocks archive file reads.

At the documented recipe's baseline, changing `riseGauge` from 8.875 to
19.125 mm emitted `37826d503ac08c16a39bf437cd263f3e488ef237104dfe20814f80397a90b0e9`,
identical to the frozen native candidate. The registry and direct
writer refused the edited input before creating a destination directory
or modifying an existing path or stream. Four process contrasts refused
other metadata, another parameter change, an unrecognized contract,
and a native-saved legacy appearance profile before creating output.
This command is research only.
See the [integration evidence and remaining gates](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#strict-sdk-json-height-edit).
