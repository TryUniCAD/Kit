# Generate a saved cuboid body graphics contrast

The [research command](../../../../re/Fusion/SavedCuboidRoundTrip/GenerateBodySceneContrast.py)
takes an independently authored semantic request from the
[#337 distinct-appearances generator](https://github.com/TryUniCAD/Kit/pull/337).
It checks the existing dependency's exact revision and generates the
parametric cuboid, parameter bindings, snapshot, named camera, and
configuration envelope from JSON. It then constructs the body graphics
from the solved geometry and generated Design graph. The emitter receives
no vendor archive.

```text
python -B re/Fusion/SavedCuboidRoundTrip/GenerateBodySceneContrast.py PinnedDependencyCheckout Request.json NewEvidence --written-at 1795824000
```

Use a clean isolated checkout of #337 at
`bb22f5b434fbb056a7bd0960d5286eefe8c88568` and a new evidence directory.
The command writes `Control.archive`, `Candidate.archive`, strict
`Document.json`, and `Generation.json` after successful verification.
The archives contain actual Fusion format bytes. The suffix keeps this
research output outside the public writer entry point.

The scene adds one live solid group. The emitter resolves the body's
Design entity, derives 12 edge and six face bounds from the prism, and
orders the leaves by the physical typed history slots. It preserves
the distinct physical and visual material owners in Design. This
research scene has zero-LOD leaves and a uniform body style scope.
It has no per-face style or picking qualifiers.

All three preregistered cases passed exact typed scene readback and
strict SDK JSON round trip. The [research record](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#source-free-body-scene-contrast)
binds the archive digests. Loaded appearance, aggregate bounds, sketch
and work geometry, picking, previews and the exact native lifecycle
remain open. Historical or unrecognized saved-source fields remain
outside the request contract. Public emission remains disabled for
this saved-profile route.
