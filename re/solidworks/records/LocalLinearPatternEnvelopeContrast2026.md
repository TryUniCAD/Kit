# Prospective linear-pattern direction point contrast

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`. This is a disclosed native source calibration design for SOLIDWORKS 2026 SP05.2 build 34.5.2.0604. No CAD launch, authoring, save or reopen was performed for this design. The prospective experiment tests the source envelope of the point in `moLPattern_c.f1288.fc8`. It does not qualify an oblique neutral reader or a writer. [Prior point observation](LocalLinearPatternTypedArchive2026.md) · [Independent geometry and authored intent](../../tooling/sw2026/linear_pattern/PatternEnvelopeSpec.py)

The principal X and Y cases discarded exactly the axis along which a replica could extend. An overhang along that axis alone cannot move the point after projection. The new case uses an oblique normal `(1,1,0)/√2`. A plate from X=0 to 120 mm and Y=0 to 90 mm has thickness 5.75 mm. The positive blind seed runs from X=87 to 98 mm, Y=34 to 43 mm and Z=0 to 12.25 mm. The two instances stay separate from one another and overlap the common plate. At spacing 20 mm the replica stays wholly over the plate. At 36 mm its X extent reaches 123.4558441227 mm and its X overlap with the plate is 7.5441558773 mm. Its Y extent remains inside the plate.

The independent geometry script measures the union by partitioning the three box domains into occupied cells. It derives volume, exterior surface area, centre of mass and exact bounding box in metres for both spacings. The projected pre-pattern midpoint is approximately `(7.5,-7.5,6.125)` mm. The projected final midpoint of the 36 mm arm is approximately `(8.36396103,-8.36396103,6.125)` mm. The hypotheses differ by 1.2218254069 mm. The 20 mm arm shares the same pre- and post-pattern envelope and serves as the internal placement control.

## Authoring and observation

1. Use an unused disclosed destination with the same pinned executable and library metadata as the previous source batch. Bracket with the existing pristine native part controls. Retain the exact build, phase errors, warnings, dialogs and process creation identities.
2. Author both positive blind profiles locally from the new specification. Reuse the verified `InsertAxis2` intersection of Right and Top, then constrain the oblique reference plane about that hinge with the documented angle and coincident modes. Verify the actual datum identity, normal and through-origin transform. Set the pattern reversal from its measured normal to give the prospectively chosen positive X and Y direction. If the datum resolves outside the two signs of the specified normal, stop and record the native observation before creating a pattern. [Measured oblique plane authoring helper](../../tooling/sw2026/oblique/AuthorObliqueCylinder.py)
3. After creating the seed and before creating the pattern, measure the joined solid's six true extreme coordinates and volume. Select the real seed at mark 4 and the oblique plane at mark 1, check their persistent identities, then create the ordinary one-direction feature pattern at 20 mm. Confirm both actual driver identities, a single body and the expected geometry. Save the source and reopen in a fresh process.
4. Reopen the same immutable original in a separate editable process and change only its actual pitch dimension to 36 mm. Keep the signed normal, count and relevant features unchanged. Require a clean rebuild, exactly one solid, full independent geometry and clean save to a new derivative. Fresh-reopen the derivative and repeat the geometry and ownership checks before the trailing control. The existing contained-profile analytic observer needs the new union predictions for the overhang arm. [Existing live pattern author and edit helpers](../../tooling/sw2026/linear_pattern/LinearPatternAuthor.py)
5. Decode the typed direction owner from both hash-pinned native saves once the newer reference layout is proved. Bind the direction plane and selected line identity before reporting the stored point. Compare the point against both fixed hypotheses, against the initial source's point and against the observed envelope extrema. A point outside both tolerances leaves the meaning open. If the unmeasured oblique reference schema refuses, retain the actual class boundary. Native source-plane identity and even a clean authoring result cannot settle the point without this archive evidence.

The spec generator outputs authored values and independent expectations only. Its current JSON SHA-256 is `a55fd0df1898f3132f1c1eba173f7ff5b8a8e1d12159e5ae9d9e91af43586287`.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/PatternEnvelopeSpec.py
```

## Frozen disclosed packet

[The staging tool](../../tooling/sw2026/linear_pattern/PatternEnvelopePacket.py) accepts the exact `LinearPatternSourcePacket03/Packet` as its control and registered API evidence. That original packet's SHA-256 is `913426870bc64edb320e6a1508521c81da677a2ef4feef80b715c7859856c1bc`. The reused pristine control SHA-256 is `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`. The new manifest binds each selected source and metadata file, the committed new and reused observer modules, the analytic specification and the exact guest location. Stage to an unused directory on the managed host share. The sealed cohort is outside the packet and the new entry point has a single disclosed run path.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/PatternEnvelopePacket.py \
  --prior-packet /absolute/share/LinearPatternSourcePacket03/Packet \
  --output /absolute/share/LinearPatternEnvelope01 \
  --guest-root '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\LinearPatternEnvelope01' \
  --guest-python 'C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe'
```

`Recipe.json` contains the exact `prlctl exec 'Windows 11' --current-user` argument arrays. The root-owned oracle runs `verify` first. The metadata phase only reads the registered version-34 type libraries and checks the installed hashes and the actual angle and axis APIs. Running `run` repeats the preflight and requires an idle oracle. The native sequence is control before, author, pristine reopen, spacing edit, spacing reopen and control after. Both saves are bound immediately at the return from native SaveAs3, again after the process exits and again during audit. Each fresh native process records the executable hash and creation FILETIME. Open, rebuild, per-feature and save warnings must be zero. The observer also rechecks the actual input selection objects and registered constraints of the oblique datum. A failed candidate stops dependent phases and retains the trailing control once the oracle is idle. [Native runner](../../tooling/sw2026/linear_pattern/RunPatternEnvelope.py) · [Observer](../../tooling/sw2026/linear_pattern/AuthorPatternEnvelope.py)

A host-only audit accepts the final lifecycle receipt by digest and independently rehashes the control receipts, both native save checkpoints and both fresh-reopen measurements. It links the actual Config-0 map to the ResolvedFeatures stream. The research overlay covers the current angle-plane and two-plane axis records in the existing documented grammar. It checks exact Resolved re-emission in memory, the seed and datum links, both creation logs and the measured signed direction. The current line wrapper ends with its model point, direction and flag. The recorded 24-byte point span is computed from that typed object's end and checked against the linked grammar and IEEE-754 values. The capture reports the actual three doubles and their original little-endian hex. No position scan or file output from the archive codec is involved. A new unsupported schema produces an explicit decoder refusal for that saved artifact. [Typed point audit](../../tooling/sw2026/linear_pattern/AuditPatternEnvelope.py) · [Scoped native layout overlay](../../tooling/sw2026/linear_pattern/PatternEnvelopeWire.py)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditPatternEnvelope.py \
  --trial /absolute/share/LinearPatternEnvelope01 --packet-sha256 TRIAL_SHA256 \
  --result-sha256 NATIVE_RESULT_SHA256 --output "$(mktemp -d)/EnvelopePoint.json"
```

The comparison uses a fixed 5 nm positional tolerance. It first requires the short-spacing point to agree with the coincident pre- and post-pattern prediction. If the edited point follows the new projected final envelope, the result supports post-pattern geometry for this case. If it remains at the initial point, the result cannot distinguish recomputation from the pre-pattern envelope and retention of the previous point. A third value or an archive refusal leaves the rule open. The individual double values remain present in every typed observation. The newly scoped oblique wire rules remain provisional. A successful capture does not qualify a constructor, a general oblique reader or the writer.

The host has verified syntax, independent predictions and the typed capture boundary on both prior disclosed principal saves. Their original `fc8` span is `25616–25640` in each Resolved stream. Both replays are exact and report the prior eight compatible display cells. The actual oblique lifecycle and point measurements await the root-owned oracle.
