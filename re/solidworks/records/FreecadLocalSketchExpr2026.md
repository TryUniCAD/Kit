# Native FCStd local sketch expression links

Workstream `B04-SW2026-CORPUS/LOCAL-SKETCH-EXPRS`, PR #121 prerequisite. The isolated reader change starts from accepted main `f3d8760f214d65fbe71aa4b8bf81a17f553dbb60`. Source case identities `C130-P01`, `C123-P01` and `C017-P01` were pinned by the disclosed public writer census before the reader implementation. [Exact process evidence](../measurements/2026/FreecadLocalSketchExpr01.json)

All three original archives have an actual `PartDesign::Pad` with a whole-object `Profile` link to the internal object `Sketch`. The published constraint owner already identifies `freecad:parameter:Sketch:constraint:9`. Its authored name is `width`, its saved value is 40 mm, and its active driving constraint owns the typed parameter. The Pad's saved `Length` is 20 mm and its native `ExpressionEngine` supplies `Sketch.Constraints.width / 2`. The baseline keeps the text and both values with an empty dependency list. The revised reader links the existing width ID before calculating the native replay digest. The legacy visibility digest retains its historical projection. Existing explicit-suppression carriers use a distinct pre-binding parse to restore their bytes.

Each pair uses fresh processes and the original source path. The guard permits reads of that file and Python implementation code. The whole returned document agrees after neutralizing the new link, its resolved-reference diagnostic and the derived native replay digest. The stored digest independently equals the observed model's digest. Original archive hashes match before and after. Each new worker restores the actual baseline carrier to its original bytes in memory and rejects exact replay once the carried sketch is edited. Pre-marker carriers migrate their hidden sketch to explicit suppression with exactly two observed native parses and an updated matching digest. If an earlier complete pre-binding parse is already cached under the same source root, path and hash, replay checks its digest and performs zero further archive parses in these three cases.

The shared `NativeObject` record lives in the archive nodes module. The previous `Native.NativeObject` name resolves to the same class. The Pad extractors import that record directly, removing the type-only back edge to the native decoder identified by the first queue analysis. [Exact queue diagnostic](https://github.com/TryUniCAD/Kit/actions/runs/44868681148/job/136738067441) · [Type-only decoder imports](../../../Documentation/Gotchas/Tooling/TypeOnlyDecoderCycles.md)

Stored interchange snapshots retain their recorded parameter graph. Native
replay verifies that graph against its historical digest. The normal SDK
writer restores all three marked and all three unmarked carriers to their
original FCStd bytes. A strict native read of each emitted archive binds
the source width ID, with its original formula and millimetre quantities.
Updating a stored interchange snapshot requires a separate migration.

The bounded rule requires a whole same-sketch profile, a unique active named driving length dimension and corroborated saved quantities. The reader indexes named dimensions once per referenced sketch, including when multiple Pads refer to its constraints. The separately authored queue process cases vary the internal name and divisor, compare a display label, and cover stale length, duplicate aliases, inactive and reference-only dimensions, and subelement links. The C130 in-memory stale-formula contrast gives the same strict-read diagnostic, formula text and saved value on both revisions. The normal strict SOLIDWORKS write leaves the destination untouched.

Run the method from a checkout containing the baseline Git object and this reader. Supply the custody-preserving existing disclosed census root and a new output path.

```sh
python3.14 -I -B re/tooling/sw2026/VerifyLocalSketchExpr.py \
  --census /path/to/disclosed/census --output /tmp/FreecadLocalSketchExpr.json
```

This work generates zero native products and grants zero corpus conversion credit. The original 165-part and five-assembly inventory and the separate SOLIDWORKS source transfer remain open.
