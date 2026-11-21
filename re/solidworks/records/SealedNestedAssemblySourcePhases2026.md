# Run sealed nested assembly source phases

The nested SOLIDWORKS 2026 source lock uses a disclosed cohort and two sealed holdout slots. The phase runner accepts the existing original source deck as an opaque guest path and SHA-256. It reuses the pinned native author, read-only reopen observer, and corrected assembly-load classifier. Each holdout has a separate before control, author, reopen, after control, and guest-local lock. A transport timeout therefore leaves finished phases and any already saved source hashes available for the next invocation. [Source cohort](NestedAssemblySourceProtocol2026.md) · [Indexed load progress](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Assembly/IndexedComponentLoadProgress.md)

## Prepare the tools on the host

Use an unused private packet directory on the VM share. Supply the original manifest's absolute Windows path and existing hash through the oracle owner's custody. The host freezer copies ten pack-bound Python tools, writes `SealedPhases.json`, and verifies the frozen tool identities in a separate process. The original deck and native input files are opened only from the guest.

```sh
python -B re/tooling/sw2026/RunSealedNestedSourcePhase.py prepare "$NESTED_PHASE_PACKET" \
  --source-deck "$NESTED_GUEST_SOURCE_DECK" --source-deck-sha256 "$NESTED_SOURCE_DECK_SHA" \
  --guest-private-base 'C:\KitOracle\NestedSealed'
```

The oracle owner uses the returned `packet_sha256` and the guest path to this new packet. For slot 1 and trial `T01`, run each guest `before`, `author`, `reopen`, `after`, and `lock` command independently in that order. Slot 2 uses `2` and `Slot02` with its own phases. Use the pinned guest Python and the owner's serialized transport. The example runs the author phase.

```sh
python -B re/tooling/sw2026/RunOracleBatch.py --vm 'Windows 11' \
  --progress-root "$NESTED_PHASE_PACKET/Progress/Slot01/T01/author/1" \
  --report "$NESTED_PHASE_PACKET/Slot01Author01Host.json" \
  -- "$NESTED_GUEST_PYTHON" -B "${NESTED_GUEST_PHASE_PACKET}\\Tools\\RunSealedNestedSourcePhase.py" \
  run "${NESTED_GUEST_PHASE_PACKET}\\SealedPhases.json" --packet-sha256 "$NESTED_PHASE_PACKET_SHA" \
  1 T01 author
```

Use an unused progress root and transport report for every phase. The runner creates `Progress/Slot01/T01/<phase>/<attempt>/Record.json`. Case data, COM calls, native paths, and artifacts stay under the packet hash and trial on the fixed guest-local drive. Shared records carry opaque slot and trial identifiers, coarse timing and status, pinned process identities, and SHA-256 receipts. The saved artifact manifest includes names, lengths and per-file digests on the guest. Only its aggregate digest appears on the share.

## Resume and lock

- `before` and `after` independently measure the same pinned healthy native part in fresh processes. Once the oracle is idle, collect `after` even when a candidate phase timed out. The tail result remains available as a control observation.
- `author` measures the native edit and restoration, saves dependencies in order, and checks their hashes. It creates a private `SavedAuthor.json` and publishes its digest and the native manifest digest before closing the oracle. A successful phase also requires clean cleanup and a second digest check. Use a new trial for an author retry so all earlier checkpoints remain available.
- `reopen` requires a passed author in the trial. It opens the exact saved root read-only, checks the hierarchy, dependency stamps, transforms, driving dimensions, and geometry, rebuilds, and rehashes the artifact set. For a reopen retry use `--attempt 2` with the same trial, followed by matching `after` and `lock` attempts. Each retry uses a fresh process.
- `lock` is a guest-local offline check. It requires four passed, chronologically bracketed phases from distinct SOLIDWORKS process lifetimes, then revalidates private phase receipts and unchanged native artifacts. The shared record publishes `heldout_source_locked: true` and the resulting digests. It starts zero SOLIDWORKS processes.

Authoring the nested writer can begin once the native locks for both sealed slots and the disclosed source cohort are recorded. The holdout designs, outputs and measurements remain sealed for subsequent writer qualification. This source protocol establishes zero generated writer outputs.

Host process verification froze the ten tools against a deliberately nonexistent guest file locator, rejected a changed observer, and rejected a native phase on the host before creating its progress directory. Native execution and source lock remain pending. [Phase runner](../../tooling/sw2026/RunSealedNestedSourcePhase.py) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Qualified pre-writer locks

Both sealed slots completed their independent before, author, reopen
and after phases. Eight distinct native process lifetimes passed.
The two lock commands checked their private artifacts and original
phase receipts and published only the resulting hashes. Slot 2's
lock command followed a transient host session failure before invocation.
Its four completed native phases were retained.

The combined source lock binds the two disclosed sources, the two
sealed native artifact manifests, both specification hashes and all
phase and transport hashes before nested writer implementation.
[Pre-writer source lock](../v2026/heldout/NestedAssemblySourceLock01.json)
