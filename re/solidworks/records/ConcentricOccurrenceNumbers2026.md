# Preserve explicit occurrence reference numbers

Task `B04-SW2026-MATES-CONCENTRIC/occurrence-number`, owner `assembly_frontier`, delivery PR #121. In normal D01 public readback, `ConcentricD01Child-1` and `ConcentricD01Child-2` carry explicit `reference_number` values `"1"` and `"2"`. The typed component index independently supplies those same strings from actual `swReferenceNumber` integers. The first occurrence is fixed and both select the same `Default` child configuration. Previously the shared neutral assembly gate rejected both explicit values. The writer already emitted the same numbers by splitting the canonical positive suffix of the binary occurrence name. [Instance index field rule](AssemblyInstanceTree2026.md)

The [shared occurrence guard](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Model/CheckAsmOcc.py) now uses the [same suffix parser](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Xml/ReadOccName.py) as the XML writer. It accepts a supplied string only when it equals the canonical number. Storage still comes from the actual generated name, so equality at admission proves the explicit value survives. Unsupported provenance and attributes still fail closed. An empty string continues to derive the number from the name.

## Revision-bound disclosed proof

The [process driver](../../tooling/sw2026/para/concentric/ProveOccurrenceReferenceNumbers.py) first reads the exact disclosed D01 parent and child, reconciles the neutral occurrence names and numbers with the native index, and verifies the actual selected side face. It also confirms that the unaltered source still fails whole-source `ReadAsmModel` admission. It constructs an independent neutral discriminator with new IDs, the two checked occurrences, their actual poses and a fresh analytic cylinder/mate. The portable discriminator uses a newly constructed child with the measured radius and depth and a separately projected child light scene. It does not carry a source archive or a previously authored template into construction. The parent presentation and unprojected source metadata remain outside this scope.

| Bound artifact | SHA-256 or revision |
| --- | --- |
| Before SDK tree | `8f9dc37d3d5d6acfc7b28a22a29c11f648643a3d` |
| Only substituted SDK file, `CheckAsmOcc.py` | `036ecc19d2306e358752ed32b34744776318ff166c056a75b5fb621b1a11469b` |
| Process driver | `69c8b8e891566a67f7698ffc0751ae12e2a49a789ce6fa57dd927fdd757d4d21` |
| D01 parent | `2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2` |
| D01 child | `92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa` |
| Independent neutral request | `d4d82d7d27e52ac5973134c6f31aeb893317530b51dbabe25803dc38a4df8bc1` |
| Generated parent, all successful variants | `8d37dcbacf3833af28975ce45be7767b996929d44d16037578e83639e24c6786` |
| Generated child, all successful variants | `6f1c33af64a074b2927abbd9019f839bac32db5b52f307a66646695f4485f69a` |
| Generated public read receipt | `90857be9981f6c2a726e703832ebfdcacc49f355157ffbc34fb2871fb69b1dbe` |

The isolated driver covers seven admission processes. The before snapshot rejects the explicit form. The after snapshot accepts explicit `"1"`/`"2"` and still refuses a mismatch, the alias `"01"`, and an unknown attribute. The before and after omitted-number cases and the after explicit-number case produce the same two archives. Each successful case performs two guarded constructions with zero runtime file, process or network attempts and eight byte-exact linked-stream comparisons per construction. A fresh normal public process reads both names, both numbers and both selected configurations from the output. Its mate retains the expected pre-solve refusal.

Run the driver with `project --parent D01_PARENT --child D01_CHILD --output NEW_REQUEST_ROOT`. In a fresh process use `--sdk-root SDK_SNAPSHOT build --request REQUEST --sha256 REQUEST_HASH --revision BASE_COMMIT --variant explicit --output NEW_BUILD_ROOT --written-at 1816308507 --destination 'C:\KitConcentricRefNumberProbe01\ConcentricD01AlignedFree.SLDASM'`. Substitute `omitted`, `mismatch`, `noncanonical` or `unknown` for the corresponding variants. The normal parent readback uses [ReadConcentricPublic.py](../../tooling/sw2026/ReadConcentricPublic.py) with `mode=default` and the generated parent hash.

## Remaining D01 owners

Both native public definitions currently display the assembly basename, although the resolved child and occurrence references identify the actual `ConcentricD01Child` file. The native resolved `Mates` folder exists, and the public graph has no mate-group row for this source. Its child body exposes the `Solid Bodies` folder fallback. These owners, the remaining root inventory and display/scene state, and the complete source-side topology correspondence still need their own semantic projection. This probe started no SOLIDWORKS processes, accessed no held-out files and establishes no source-wide admission or native acceptance. [Root audit](ConcentricParentRootAudit2026.md) · [Source admission prerequisites](ConcentricSealedAdmission2026.md)
