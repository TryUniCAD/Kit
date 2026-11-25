# Saved cuboid public boundary evidence

This is deterministic SDK and process evidence against reader revision
`cbd5b5d7552c0bb29f56153da933fe1fa2650dfb`, using Python 3.14.6 on Windows.
It does not establish native acceptance for newly emitted archives, semantic
editing, or source-free generation from saved native state.

## Source custody

[Corpus/Manifest.json](Corpus/Manifest.json) pins four prior captures and their
original native stage records. The controls were authored independently in the
prior Fusion oracle run; the edited/restored baseline archives were saved in that
prior run. Their copied records retain the original build, process, stage and
archive hashes. No new vendor run is claimed by these fixtures.

The public compatibility checks live under
[tests/Convert/Api/Fusion/SavedCuboid](../../../tests/Convert/Api/Fusion/SavedCuboid).
The normal complete-suite collection, merge-queue planner and shards discover
these tests without a separate workflow or native application runner.

## Observed checks

- 17 public SDK integration cases passed: four strict reads with persisted
  complete JSON, four constraint/parameter/identity cases, seven unsupported
  native mutations, and two read-only publication refusals including attempted
  removal of the read-only flag. Existing destination bytes remained intact.
- Four fresh `python -m KitCli decode` processes passed in 38.08 seconds outside
  the restricted sandbox. Each complete neutral output equals the SDK read and
  retains `fusion.read_only`. Earlier sandbox runs failed at atomic JSON rename
  with Windows error 5, including a workspace temporary directory; these failures
  are not represented as successful process checks.
- The public boundary harness persisted JSON for all four captures, then received
  the expected `AdapterNotFoundError` at public no-carrier native writing.
  It retained the native-state contract and read-only flag throughout.

`PublicBoundaryCheck.py` accepts repeated `--source` and an unused `--output`
directory. With this reader-only boundary it preserves the complete document
JSON and report, and exits 3 to keep native writing explicitly unqualified.
Example from the repository with its SDK on `PYTHONPATH`:

```powershell
python re/Fusion/SavedCuboidRoundTrip/PublicBoundaryCheck.py `
  --source re/Fusion/SavedCuboidRoundTrip/Corpus/BaselineEdited.f3d `
  --output C:/Unused/SavedCuboidBoundary
```

The measured report is retained locally at
`.rescratch/FusionSavedPublicBoundary02/Report.json`; its SHA-256 is
`c2d7c81d500b48879a8dd0f40229368a95f6fcd86d1c4477b3310a1b74ad02fb`.

| Capture | Persisted complete document SHA-256 |
| --- | --- |
| BaselineControl.f3d | `fa1eb59a302e12505e5968f35c394de598a292fa2281645fe0dc7b7d16b423f3` |
| BaselineEdited.f3d | `3322e5baeff2412c780486892840531b3f852d9b70497aa5deba53194fed8a7b` |
| BaselineRestored.f3d | `e25c096e68c92a55312b55c2a2dbeddd33045b39db4cd1b0f7b59d1b53fc99d3` |
| HoldoutControl.f3d | `9498a9842e8485a01671f0d2a8997c68319657c61110a78a2f702b7991a63bab` |

## Preserved state and unfinished boundaries

The complete typed native model survives strict public projection and persisted
JSON equality, including the semantic graph, native history, `PrismSnapshot`,
`GraphicScene`, material, two preview parts, empty configuration rule/table
sidecars and empty images folder. Graphics bounds may retain an earlier height
in the vendor-saved source. The unchanged contract preserves that actual typed
state and does not use graphics as authoritative BRep geometry.

The neutral sketch preserves its fixed corner and distinct fixed construction
origin as point properties, four real horizontal/vertical rules and two driving
size dimensions. It does not invent a coincidence or fixed-rule record. Seven
parameters, their original IDs, driver expressions and attachment relationships
remain present.

The new fixed-corner route is deliberately read-only. Lower typed native
re-emission equality alone is not a generative writer or native lifecycle
acceptance. Changes to saved semantic parameters, history, snapshots, graphics,
material/cache state and every other dependent field remain gated on complete
closure and independent fresh-process native measurements. Existing unsupported
families and native-state guards stay in force.
