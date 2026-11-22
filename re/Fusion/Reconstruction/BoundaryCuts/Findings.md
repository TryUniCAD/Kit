# Rectangular boundary cuts

These are independently API-authored research controls, not donor data for a writer and not conversion acceptance.

## Capture and deterministic inspection

Run `cad-api script fusion CaptureControls.py --output NEW_DIRECTORY` through the private owner service. The script creates four cut variants bracketed by healthy base solids, captures native geometry and feature observations, edits each cut depth to one half, measures it, restores it and measures again. Every owned document closes.

Run `PYTHONPATH=src python re/Fusion/Reconstruction/BoundaryCuts/DecodeHistory.py re/Fusion/Reconstruction/BoundaryCuts/Controls OUTPUT.json` from the checkout with Python 3.14 and installed runtime dependencies. The inspector reads the committed sibling NativeObservations.json or the fresh API directory CutCorpus.json.

## Observed joins

The timeline has two sketch/extrude pairs. The create extrusion owns one DcBody through dcBodies. The cut has an empty dcBodies collection; its targetDataRefs resolve through a ModelDataRef to DRBody.refBodies, which identifies the original DcBody. The cut changes the existing body rather than creating another one. startModelHS equals the prior extrusion endModelHS. Each distance and taper role resolves through its own DcDoubleParameter to its Parameter.

The first original control has state 5 volume 24 cm³ and state 6 volume 22 cm³. Held-out dimensions and an opposite corner give different volumes. A partial-depth pocket has nine faces rather than eight.

## Actual evidence and remaining gaps

All six controls captured successfully. Both healthy controls measured 24 cm³. The four cut archives decoded through the typed native document and journal readers. Their closed-shell ownership, edge mating, line geometry, plane membership, outward face area and Euler characteristic were checked. Signed boundary integration matched independently measured native volume, area, face/edge/vertex counts and minimum/maximum bounds for every cut within 1e-9 relative and absolute tolerance. See NativeObservations.json and DecodedHistory.json for hashes and exact observations.

This research inspector does not establish polygon self-intersection freedom or complete semantic coverage. It does not replace the strict neutral decoder. That decoder still refuses these histories. Complete sketch constraints, live boolean operands, feature definitions, general nonconvex geometry validation, source round-tripping and vendor acceptance remain unfinished. No refusal was removed or hidden to obtain these measurements.
