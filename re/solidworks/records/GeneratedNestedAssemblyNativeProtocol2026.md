# Measure the first generated nested assembly bundle

The frozen trial binds generated LinkPlate, OffsetModule and TiltFrame files to writer revision `aa245b58e0dc9857f07e68aafa9727925ec52386`, the completed pre-writer native source lock, an independent neutral-geometry prediction, and the exact original N01 disclosed source. The guest runner supports four separate phases. Each phase has its own transport and output directory, allowing the trailing native control to run after a candidate failure once the oracle is idle. [Generation evidence](GeneratedNestedAssembly2026.md) · [Trial lock](../measurements/2026/GeneratedNestedAssemblyTrialLock01.json)

## Freeze and verify

Run `InspectGeneratedNestedAssembly.py prepare` with the exact disclosed results directory, the private generated build directory and an unused private packet named `GeneratedNestedAssembly01`. Supply the committed writer revision. The freezer checks the versioned public source lock and generation receipt, independently recomputes the prediction from the neutral request, checks every writer tool hash, and copies the three generated files and thirteen oracle tools. A separate process verifies the frozen packet. The complete generated originals remain under `FrozenGenerated`. [Observer and freezer](../../tooling/sw2026/InspectGeneratedNestedAssembly.py)

```sh
python -B re/tooling/sw2026/InspectGeneratedNestedAssembly.py prepare \
  "$NESTED_DISCLOSED_RESULTS" "$NESTED_GENERATED_BUILD" "$NESTED_NATIVE_PACKET" \
  --writer-revision aa245b58e0dc9857f07e68aafa9727925ec52386
```

The pinned first packet SHA-256 is `efc1cae76b8c7b0b6c0a9913e759248e32aa5ac4a15f0591a11aefd798dded53`. Its observer SHA-256 is `80cace6237aae82b1b9fc4ec223540e37b9e7f0a36f6b5796bee01d59ee89bf9`. The host verifier passed. A host invocation of the native entrypoint was rejected before creating either the native working directory or Inspection. A disposable copied packet with one changed native file failed custody verification.

## Execute one phase at a time

The sole oracle owner invokes the frozen tool through the serialized Windows transport. Use `before`, `generated`, `reopen` and `after` in that order. Each call uses a fresh unused `Inspection/<phase>` progress root and separate host report. The generated phase requires the before control to have passed. The after control can run independently.

```sh
python -B re/tooling/sw2026/RunOracleBatch.py --vm 'Windows 11' \
  --progress-root "$NESTED_NATIVE_PACKET/Inspection/generated" \
  --report "$NESTED_NATIVE_PACKET/GeneratedHost.json" \
  -- "$NESTED_GUEST_PYTHON" -B "${NESTED_GUEST_PACKET}\\Tools\\InspectGeneratedNestedAssembly.py" \
  run "${NESTED_GUEST_PACKET}\\Trial.json" \
  --packet-sha256 efc1cae76b8c7b0b6c0a9913e759248e32aa5ac4a15f0591a11aefd798dded53 generated
```

Both native controls reopen the exact saved N01 root at its original path with its original siblings. They use the existing disclosed hierarchy and source observer. The generated lane uses its own independently predicted part lengths, mass properties and transforms. All generated definitions must have one active independent Default configuration. The leaf must expose both authored sketch dimensions and its driving extrude depth.

The generated phase copies the immutable originals into the exact encoded `GeneratedInput` sibling directory. It opens the root without preloading dependencies, records all open statuses, and walks every resolved child through its actual physical file, configuration, native name and root-context transform. Each leaf supplies one visible solid. It checks the per-definition native feature trees and warning counts, driving parameter values, volumes, areas and centers of mass. It measures these properties before and after a dependency-ordered rebuild.

The driving edit changes LinkPlate's depth from `0.0068 m` to `0.0103 m`. After rebuilding the part, module and root in that order, the observer requires the independently computed edited geometry throughout the hierarchy. It saves those three owned working files in dependency order and verifies every earlier-saved child's hash and update stamp across the later owner saves. The recorded native working files form an edited derivative. The frozen generated files retain their original hashes.

The fresh `reopen` phase opens the edited root read-only in another process. It checks the same paths, counts, names, transforms, driving values, geometry and persisted dependency stamps before and after rebuild. Both controls remain prerequisites for a qualified native result.

## Result boundary

After the final control, run the frozen tool's `summarize` mode with the same manifest and digest. It writes `Inspection/NestedAssemblyResults.json`. The result binds all phase records, the writer revision and tool identities, the independent prediction and source lock. Passing requires all four phases, four distinct native process lifetimes, chronological brackets, intact frozen inputs and unchanged synchronized derivatives. A failed or missing phase remains explicit in the result.

The four native phases passed with healthy brackets, intact originals and synchronized saved derivatives. Open, rebuild, a live 6.8 to 10.3 mm leaf-depth edit, all three saves and fresh reopen passed. The first host summary used Python 3.9 and failed on `zip(strict=True)`. Offline summary execution under Python 3.11 passed using the same completed native records. This trial exercises the authored visible, resolved, rigid three-file prism hierarchy. The separately sealed sources retain their independent qualification role. [Measured result and runtime correction](GeneratedNestedAssemblyNative2026.md)
