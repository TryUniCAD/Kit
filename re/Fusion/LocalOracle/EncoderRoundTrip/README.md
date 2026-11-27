# Fusion encoder cuboid oracle

This research harness measures an exact encoder candidate in licensed Fusion. It
authors its own reference cuboid through the Fusion API and never supplies that
archive to the encoder. The harness does not run inside conversion.

Prepare each run in a new directory. Select the corresponding case dimensions
and encoder output role.

```text
python re/Fusion/LocalOracle/EncoderRoundTrip/Prepare.py baseline PATH/edited.f3d PATH/baseline-edited --source PATH/source.f3d --role edited
python re/Fusion/LocalOracle/EncoderRoundTrip/Prepare.py holdout PATH/reconstruction.f3d PATH/holdout-reconstruction --source PATH/source.f3d --role reconstruction
```

| Case     | Width × depth  | Original height | Encoder edit | Native edit |
| -------- | -------------- | --------------- | ------------ | ----------- |
| Baseline | 16.4 × 27.1 mm | 13.8 mm         | 22.6 mm      | 28.3 mm     |
| Holdout  | 43.7 × 12.9 mm | 24.6 mm         | 31.4 mm      | 19.7 mm     |

Use the installed Fusion launcher and a task-owned process with no open
documents. Run each stage in order. Quit the task-owned process between stages
and start Fusion again before dispatching the next stage.

1. **ControlBefore** authors, rebuilds, exports and reopens the independent
   control at the candidate's expected dimensions.
2. **Candidate** checks the prepared SHA-256, opens and rebuilds the exact
   archive, rolls back and restores the extrusion, and edits the driving
   `kitHeight` parameter. It exports both the edited and the restored designs.
3. **Reopen** opens and rebuilds both saved variants in a new process. Skip
   this stage if the candidate did not save both variants.
4. **ControlAfter** reopens the exact control archive and rebuilds it at the
   expected height and at the independent native edit.

Dispatch individual stages with the repository's [locked bridge](../RunLocked.mjs).
If the localhost bridge is unavailable, use Fusion's **Scripts and Add-Ins**
dialog to add and run the generated stage folder. Use a new process for each
invocation, and keep the four folders outside Fusion's startup add-in folder.
[Autodesk script instructions](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm)

```text
node re/Fusion/LocalOracle/RunLocked.mjs PATH/baseline-edited/ControlBefore/ControlBefore.py --timeout 40
```

Each stage writes a JSON receipt with its process ID, Fusion build, batch
and candidate digests, observations, and any stage failure. The harness checks
one solid, the two healthy timeline nodes, the constrained rectangle and
its dimension bindings, the origin, the cuboid's exact topology, analytic
volume and area, bounds, and center of mass. Fusion measures lengths in
centimetres, area in square centimetres, and volume in cubic centimetres.
Geometry comparisons use absolute and relative tolerances of `1e-8` in
those units. A failed control invalidates the batch. Keep the four receipts
with the exact source and candidate identities when recording evidence.

When the oracle batch measured an exact shared runner artifact, create an
attachment from the saved stage receipts and the runner's manifest:

```text
python re/Fusion/LocalOracle/EncoderRoundTrip/Receipt.py PATH/baseline-edited PATH/runner-output PATH/edited-receipt.json
kit research --root KIT_CHECKOUT encoder-round-trip attach-receipt --output PATH/runner-output --role edited --receipt PATH/edited-receipt.json
```

The attachment binds the run fingerprint, SDK revision, source and candidate
hashes, and stage receipt hashes. Product qualification remains a separate
evaluation of the complete CAD success criteria.
