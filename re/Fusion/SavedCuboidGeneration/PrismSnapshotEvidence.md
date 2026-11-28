# Standalone cuboid snapshot derivation

[ProbePrismSnapshot.py](ProbePrismSnapshot.py) constructs a typed snapshot from the selected sketch and closed solid history. The snapshot links each of its four sides to the Design curve with the same endpoints. The same four identities must also occur in the closed solid history. Each sheet walks its perimeter counterclockwise from the upper-left corner, uses bounded straight segments and a centered XY plane, and assigns each vertex to an incident edge. The profile uses the lowest indexed incident edge. The sketch uses the incoming edge. The existing snapshot codec emits and reads the standalone four-byte record format.

The probe builds with the snapshot field absent. Its optional saved control mode compares the newly derived typed value with an independently decoded saved snapshot only after construction. The file input digest must match the supplied SHA-256. The probe prints measurements and publishes no archive or snapshot file.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedCuboidGeneration/ProbePrismSnapshot.py Candidate.f3d `
  ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be
```

## Measured boundaries

Each of nine cases ran in a separate Python 3.14.6 process against SDK `f77ab6a0f49af7771ce1509edec5053454985cad`. Every result round-tripped exactly through the typed snapshot codec. The three generated archives supplied no snapshots. Every saved control independently matched the complete derived typed snapshot, including the solid, two profile sheets, links, header and stamp. This includes the original, edit and restore of the 16.4 × 27.1 mm profile, an independently captured 43.7 × 12.9 mm profile, and two vendor saves of the new source-free constructor.

| Input | Archive SHA-256 | Derived standalone snapshot SHA-256 |
| --- | --- | --- |
| Generated baseline | `ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be` | `2c1ae90382ee29186faa90680dab8e2ae244185318686c069cbd11d4e6a576da` |
| Generated height edit | `8a28cf09b4e48108ca475d468b9e477314b92dfe1dedbf0715920ab0712682e3` | `64f7c4e92fbeefa9341a365eaa5e8558f0b207e7aa83ca93d6d8d2caa08bceaf` |
| Generated holdout | `f318fd94e17b42603c93135d9d6fde7691e5050f950edeee29d4be0d7a5d52b0` | `f0bacbfe606948203c89eae93bcc6a67c77b4da8c1fa60309a95b45aead06203` |
| Saved baseline control | `5f9ad382c5e4b15313a59bebe4201ccd5b87137a3f20ebe85f5e3fba79148ca0` | `7c01baeaecb0f33549a5bca632c1b1ad771e6610772ef3933a8aded5a6828d34` |
| Saved height edit | `24f2c0e7714e3c234ead298c842b118a828ac7a3d6f6b48b9f924a8af0926ac5` | `e6aab609ef896890a0efa195ae04081c925bdd183aef27b1f186746149dbd19a` |
| Saved height restore | `98341de3b091096939a86b8b00f5da016f76b2acffdd5e8ff5e2a636797972df` | `577933ed0eb77d4e8ff538facae3f9e09a427eba6bc9b6c11f452bcb901db8f2` |
| Saved independent profile | `850b1a76c30c673ba10e33ef1e78618c5e9f106646d5aa9fbf3411ddd6683ac4` | `af2269b2ad0d1b21b4947410848c914496e263ba96f127ff5d32cb236f597412` |
| Generated baseline after native height edit | `9b8f934ec40f60d6abf76379b35789b4a32a732148cef2acb1c9e7a96d499c4a` | `c014dec4750a4bbae3b0a29da617307da04fa8d253bbb21b71796d83f021e6f4` |
| Generated baseline after native height restore | `d7429b483edba58091e723daac1005b5fff0e587f4f73007930cb6cc69deb756` | `4f32e9f56a0acdaab78454ab7d3acbcc945a2470dc9a2a11875bdc07f3e75142` |

## Archive ownership boundary

Each of the six saved controls uses the snapshot UUID in the Design `BRepSerializer.partName`. It is distinct from the archive asset snapshot UUID. The serializer points to a `PassiveIdGenerator`. Its three `scanOrderIndex` entries bind the snapshot's solid, profile and sketch roots to the selected extrusion tool cache, profile cache and sketch body identity, in that order. Both caches reference the actual asset and component. The generator's `nextId` exceeds the three identities. These are verified joins. Each tested save also has three distinct nonzero `addressOfTopEntities` values. Those values vary even when the native save records the same root IDs. Their representation and whether Fusion can reconstruct those slots from fresh data remain open. No recorded values are used to construct the standalone payload.

The measured shape is one positive origin-anchored prism with one rectangular sketch. Archive-level generation still needs to produce the serializer and root-cache graph with a supported address policy, then measure its use by Fusion alongside the generated configuration and presentation state. The [earlier writer evidence](../SavedCuboidWriter/NativeSameSourceReplay.md) records the separate same-source replay boundary.
