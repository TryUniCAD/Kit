# Explicit child position in the perpendicular source cohort

Task `B04-SW2026-MATES-PERPENDICULAR`, owner `/root/assembly_occurrence`, delivery PR #121. This is a source-authoring correction after a controlled disclosed failure, not perpendicular writer work. Root alone owns the Windows oracle. The previous frozen packet, its source inputs, opaque sealed specifications and raw receipts remain unchanged.

## Measured first failure

Packet01 D01 reached the independent child geometry check after native child dimension edits, occurrence insertion and the perpendicular API call. The measured child volume `5.759662999999999e-6 m³` and area `0.0022595799999999997 m²` agree with requested dimensions `0.0379 × 0.0167 × 0.0091 m`. Its centre of mass was `(0.00105, -0.00165, 0.00455) m`; the independently authored target was `(0, 0, 0.00455) m`. The X centroid check rejected the source before a baseline assembly pair was saved.

The independent leading and trailing native controls both passed clean open, rebuild and zero warnings/errors. They and the failed author used three distinct process creation identities. Raw author receipt SHA-256 is `2cbd932cbcc5fd8728c7788494a55484ff841dadbabd2038bc42c6bd815de477`. The [sanitized attempt receipt](../measurements/2026/PerpendicularMateSourceAttempt01.json) preserves the failed outcome. No generated perpendicular writer output, qualified source lock or held-out acceptance resulted.

Only the declared D01 author record and exact original control `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57` were inspected. The control's typed sketch projection has four horizontal/vertical relations and two driving point distances, with no centering relation. Changing those lengths does not author an origin for its free XY translation. The observed centroid deltas are observations, not a correction formula or a new prediction.

## Corrected native author request

[PositionPerpendicularChild.py](../../tooling/sw2026/PositionPerpendicularChild.py) edits the existing native `Sketch1` after its length edits. It requires the ordinary under-constrained four-edge rectangle, resolves each real native sketch point from its line endpoints and `GetID`, and explicitly sets the lower-left point to the original neutral target `(-width/2, -height/2, 0)`. It verifies all four actual native corner coordinates against the original authored rectangle before closing the sketch and rebuilding. No empirical centroid subtraction, tolerance change, new parameter or changed design is introduced.

The registered metadata preflight now requires `EditSketch`, active-sketch access and `ISketchPoint.SetCoords` with three coordinate arguments and a Boolean result. An unavailable signature stops before CAD activation. The ordinary under-constrained code `2` is also documented in the independently recorded [2026 constraint-status type metadata](SketchConstraintStatesTypes2026.json). Success of the point operation itself still requires the next controlled native attempt. No native success is inferred from host parsing or metadata availability.

Packet02 pins the revised author, metadata and preparer plus the new position helper. The disclosed specification, case predictor and existing ownership/geometry observer remain byte-identical to Packet01. Its `seal` phase copies the original opaque guest-private specifications by the existing public SHA-256; it does not sample replacements or expose them to the host. The reused specification hash is `c86195e3ebd547b562d847218ee55ada42acb86e31b67ef451c02a67cf80b0e4`.

The external `PerpendicularMateSourcePacket02/Source.json` SHA-256 is `f202c1bacb349a6028ccb56be43d4881221663c0fc9a5444043da7bd01fbdb1c`; recipe SHA-256 is `dace1a07cafef272b0b28bc5288556f8210fd000510ed6134bc603d6eeaec5ca`. Host verification passed with zero native processes, zero sealed payload reads and unchanged disclosed/predictor/observer hashes. Root must run `verify` and `metadata`, then the independent controls and source phases. The original strict centroid, exact pose, full tree, actual owner/datum IDs, edit/save/fresh-reopen and immutable-input gates remain intact.

No perpendicular constructor, SDK registration or shared writer changed. The separate normal assembly registry overlay is independently frozen and does not depend on this source correction. [Original protocol and construction evidence](PerpendicularMateSourceProtocol2026.md) · [Free-translation gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Assembly/FreeRectangleResizeDoesNotKeepCentre.md)

## Exact metadata owner correction

Packet02's host fingerprint check passed, but its registered guest metadata prerequisite stopped before CAD activation because `FeatureByName` had been required on `IModelDoc2`. Root's complete registered member probe, SHA-256 `07acc52f2749bac05ab2a383b278d0b114f7cb2cc8326d2a8eab2381ccdbbf46`, identifies its actual owner as `IPartDoc`. `IModelDoc2.EditSketch` was already declared correctly. The metadata failure is not a native source or geometry result.

| Declaring interface and method | DISPID | Arguments | Return |
| --- | --- | --- | --- |
| `IPartDoc.FeatureByName` | `5` | One `VT_BSTR` name | `VT_DISPATCH` |
| `IModelDoc2.EditSketch` | `65649` | None | `VT_VOID` |
| `ISketchPoint.SetCoords` | `13` | Three `VT_R8` coordinates | `VT_BOOL` |

Packet03 changes only that metadata interface ownership. The actual part lookup, point operation, original disclosed design, independent predictor and strict observer remain byte-identical to Packet02. All fourteen tools remain pinned, with only `PerpendicularApiMetadata.py` changing to SHA-256 `425cf27d81227ecbf97c6efcc3da1de83fc8952856f38f3f7c08eb5a249bcf70`. The original sealed specification hash remains `c86195e3ebd547b562d847218ee55ada42acb86e31b67ef451c02a67cf80b0e4`, copied guest-side by hash without host payload access.

The external Packet03 source SHA-256 is `9fdfff4ee0fc960dbb70ec3058d4ac6652ba5413caf7171aa119d5b4500b4a41`; recipe SHA-256 is `60258bb60b01fd7134fa85aada4b0b6fe62bab7c5ad843ae96abd0ed6c43c4d0`. Host verification passed with zero native launches or sealed design reads. Root retains both earlier pre-CAD metadata failure attempts and all frozen packets. Registered preflight and controlled native source acceptance are separate gates and remain root-owned. [Declaring-interface gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Assembly/FeatureByNameBelongsToPartDoc.md)
