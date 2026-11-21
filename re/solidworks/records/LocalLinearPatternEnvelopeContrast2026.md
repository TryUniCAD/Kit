# Linear-pattern direction point contrast

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`. The first disclosed source attempt on SOLIDWORKS 2026 SP05.2 build 34.5.2.0604 stopped at the direction guard after three processes with two healthy controls and zero saves. The retry tests the source envelope of the point in `moLPattern_c.f1288.fc8`. Oblique neutral-read and writer qualification remain open. [Prior point observation](LocalLinearPatternTypedArchive2026.md) · [Independent geometry and authored intent](../../tooling/sw2026/linear_pattern/PatternEnvelopeSpec.py)

## First native attempt

`LinearPatternEnvelope01` used observer revision `c3bf4919cf0f5e55defa83651724a8baf3a912f0` and packet SHA-256 `f38a850c96bf8c9b4c890453b4b8e5e26beb7ca19290d0f756d4c5390ee77d8b`. The frozen spec SHA-256 `a55fd0df1898f3132f1c1eba173f7ff5b8a8e1d12159e5ae9d9e91af43586287` expected either sign of `(1,1,0)/√2` and specified travel in its positive orientation. The terminal result SHA-256 is `1332fa7d2293740ea844e2fd934085c3099849136a54e682444355576d5756b5` and the failed author record SHA-256 is `cde5e3665938f1c30ece0a75f8d8370d7e1764ec0484f12f2cc6fa5f3e6f27f6`.

Right and Top were selected in that order before `InsertAxis2(True)`. The real hinge endpoints were `(0,0,0.0128625)` m followed by `(0,0,-0.0006125000000000002)` m. The unoriented through-origin test passed. The author then selected the real Right Plane at mark 0 and hinge at mark 1 and successfully called `InsertRefPlane(16, π/4, 4, 0, 0, 0)`. Transforming the plane's local unit Z returned the model-space vector `(0.7071067811865476,-0.7071067811865476,0)` and its origin was `(0,0,0)`. The measured normal is orthogonal to the planned normal. Reversal of pattern travel could only negate the measured vector. The author stopped at `ArrayData` before creating the pattern. There was no save, readback or point measurement. [Numeric failure evidence](../measurements/2026/LocalLinearPatternEnvelopeSetup01.json) · [Directed hinge gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/ObliquePlaneFlipDependsOnDirectedHinge.md)

## Replacement prediction

The principal X and Y cases discarded exactly the axis along which a replica could extend. An overhang along that axis alone cannot move the point after projection. The retry preserves the angular command and adopts independent geometric predictions for signed travel `(1,-1,0)/√2`. A plate from X=0 to 120 mm and Y=0 to 90 mm has thickness 5.75 mm. The positive blind seed runs from X=87 to 98 mm, Y=34 to 43 mm and Z=0 to 12.25 mm. The two instances stay separate from one another and overlap the common plate. At 20 mm spacing the replica stays wholly over the plate. At 36 mm its X extent reaches 123.4558441227 mm and its X overlap with the plate is 7.5441558773 mm. Its Y extent of 8.5441558773–17.5441558773 mm remains inside the plate.

The independent geometry script measures the union by partitioning the three box domains into occupied cells. It derives volume, exterior surface area, centre of mass and exact bounding box in metres for both spacings. The projected pre-pattern midpoint is `(52.5,52.5,6.125)` mm. The projected final midpoint of the 36 mm arm is approximately `(53.36396103,53.36396103,6.125)` mm. The hypotheses differ by 1.2218254069 mm. The 20 mm arm shares the same pre- and post-pattern envelope and serves as the internal placement control.

## Authoring and observation

1. Use an unused disclosed destination with the same pinned executable and library metadata as the previous source batch. Bracket with the existing pristine native part controls. Retain the exact build, phase errors, warnings, dialogs and process creation identities.
2. Author both positive blind profiles locally from the new specification. Verify the directed `InsertAxis2` intersection of Right and Top along negative Z. Constrain the oblique reference plane about that hinge with the angle and coincident modes. Verify the actual datum identity, normal and through-origin transform. Set pattern reversal from the measured normal to give positive X and negative Y travel. If the datum resolves outside the two signs of this specific normal, stop and record the native observation before creating the pattern. [Measured oblique plane authoring helper](../../tooling/sw2026/oblique/AuthorObliqueCylinder.py)
3. After creating the seed and before creating the pattern, measure the joined solid's six true extreme coordinates and volume. Select the real seed at mark 4 and the oblique plane at mark 1, check their persistent identities, then create the ordinary one-direction feature pattern at 20 mm. Confirm both actual driver identities, a single body and the expected geometry. Save the source and reopen in a fresh process.
4. Reopen the same immutable original in a separate editable process and change only its actual pitch dimension to 36 mm. Keep the signed normal, count and relevant features unchanged. Require a clean rebuild, exactly one solid, full independent geometry and clean save to a new derivative. Fresh-reopen the derivative and repeat the geometry and ownership checks before the trailing control. The existing contained-profile analytic observer needs the new union predictions for the overhang arm. [Existing live pattern author and edit helpers](../../tooling/sw2026/linear_pattern/LinearPatternAuthor.py)
5. Decode the typed direction owner from both hash-pinned native saves once the newer reference layout is proved. Bind the direction plane and selected line identity before reporting the stored point. Compare the point against both fixed hypotheses, against the initial source's point and against the observed envelope extrema. A point outside both tolerances leaves the meaning open. If the unmeasured oblique reference schema refuses, retain the actual class boundary. Native source-plane identity and even a clean authoring result cannot settle the point without this archive evidence.

The replacement spec generator outputs authored values and independent expectations only. Its JSON SHA-256 is `c1c36fba4a7029b7f2018c663e9f5c7fc6b037ad68c03ff19c01550a749b13ba`.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/PatternEnvelopeSpec.py
```

## Frozen disclosed packet

[The staging tool](../../tooling/sw2026/linear_pattern/PatternEnvelopePacket.py) accepts the exact `LinearPatternSourcePacket03/Packet` as its control and registered API evidence. That original packet's SHA-256 is `913426870bc64edb320e6a1508521c81da677a2ef4feef80b715c7859856c1bc`. The reused pristine control SHA-256 is `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`. The tool also verifies the two failed setup receipts in the sibling `LinearPatternEnvelope01` directory. The new manifest binds their digests, each selected control and metadata file, the committed observer modules, the analytic specification and the exact guest location. Stage to an unused directory on the managed host share. The sealed cohort is outside the packet.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/PatternEnvelopePacket.py \
  --prior-packet /absolute/share/LinearPatternSourcePacket03/Packet \
  --output /absolute/share/LinearPatternEnvelope02 \
  --guest-root '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\LinearPatternEnvelope02' \
  --guest-python 'C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe'
```

`Recipe.json` contains the exact `prlctl exec 'Windows 11' --current-user` argument arrays. The root-owned oracle runs `verify` first. The metadata phase only reads the registered version-34 type libraries and checks the installed hashes and the actual angle and axis APIs. Running `run` repeats the preflight and requires an idle oracle. The native sequence is control before, author, pristine reopen, spacing edit, spacing reopen and control after. Both saves are bound immediately at the return from native SaveAs3, again after the process exits and again during audit. Each fresh native process records the executable hash and creation FILETIME. Open, rebuild, per-feature and save warnings must be zero. The observer also rechecks the actual input selection objects and registered constraints of the oblique datum. A failed candidate stops dependent phases and retains the trailing control once the oracle is idle. [Native runner](../../tooling/sw2026/linear_pattern/RunPatternEnvelope.py) · [Observer](../../tooling/sw2026/linear_pattern/AuthorPatternEnvelope.py)

A host-only audit accepts the final lifecycle receipt by digest and independently rehashes the control receipts, both native save checkpoints and both fresh-reopen measurements. It links the actual Config-0 map to the ResolvedFeatures stream. The research overlay covers the current angle-plane and two-plane axis records in the existing documented grammar. It checks exact Resolved re-emission in memory, the seed and datum links, both creation logs and the measured signed direction. The current line wrapper ends with its model point, direction and flag. The recorded 24-byte point span is computed from that typed object's end and checked against the linked grammar and IEEE-754 values. The capture reports the actual three doubles and their original little-endian hex. No position scan or file output from the archive codec is involved. A new unsupported schema produces an explicit decoder refusal for that saved artifact. [Typed point audit](../../tooling/sw2026/linear_pattern/AuditPatternEnvelope.py) · [Scoped native layout overlay](../../tooling/sw2026/linear_pattern/PatternEnvelopeWire.py)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditPatternEnvelope.py \
  --trial /absolute/share/LinearPatternEnvelope02 --packet-sha256 TRIAL_SHA256 \
  --result-sha256 NATIVE_RESULT_SHA256 --output "$(mktemp -d)/EnvelopePoint.json"
```

The comparison uses a fixed 5 nm positional tolerance. It first requires the short-spacing point to agree with the coincident pre- and post-pattern prediction. If the edited point follows the new projected final envelope, the result supports post-pattern geometry for this case. If it remains at the initial point, the result cannot distinguish recomputation from the pre-pattern envelope and retention of the previous point. A third value or an archive refusal leaves the rule open. The individual double values remain present in every typed observation. The newly scoped oblique wire rules remain provisional. A successful capture does not qualify a constructor, a general oblique reader or the writer.

The first preparation verified the typed capture boundary on both prior disclosed principal saves. Their original `fc8` span is `25616–25640` in each Resolved stream. Both replays are exact and report the prior eight compatible display cells. The host verified the replacement predictions against the original dimensional inputs. The actual oblique lifecycle and point measurements await the root-owned oracle.
