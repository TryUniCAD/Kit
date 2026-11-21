# Staged publication of owned nested SOLIDWORKS assemblies

| Ownership | Scope |
| --- | --- |
| Task | `B04-SW2026-NESTED-PUBLICATION` |
| Delivery | PR #121 takeover, from `4d7deb8495646c4e148401bb6da723ab0275d3db` |
| Dependencies | Neutral nested preparation, the existing assembly option and native path policy, and the shared registry path transaction |
| Exit | Exact publication of every prepared file, controlled rollback and unchanged flat output |
| Remaining product gate | Controlled native lifecycle and held-out qualification of the neutral staged route, then normal writer selection |

## Transport

The internal `WriteNestedAsm` call creates a private registry with one
locally constructed adapter and delegates to the usual checked staged path
entry. The existing registry supplies the authoritative host final path.
The current assembly option parser handles overwrite, configuration and
destination-format requests. The logical Windows path uses the existing
`native_destination` option and agrees with the actual root filename.
Non-root names come from the ordered neutral definition plan. The emitter
checks each one against the Windows sibling policy, scans the final directory
for case-folded collisions and matches the complete prepared file set before
opening any staged file.

The flat and nested emitters share exact exclusive file writes and byte
accounting. The registry commits the requested assembly and all staged
companions using its usual per-file exclusive operation. Its identity-based
rollback removes this call's earlier outputs after a handled failure and
preserves a peer's existing file. The two tests fail the final companion
after three earlier publications. Overwrite remains closed for this
profile. The direct callable keeps both native usability flags false.
[Shared transaction](../../../Documentation/Reference/Architecture/Engine.md#path-destinations) ·
[Dangling root guard](../../../Documentation/Gotchas/Conversion/Commands/DanglingBundleTargetsNeedLexicalCheck.md)

## Host measurement

| Disclosed neutral recipe | Published files | Bundle bytes | Match |
| --- | ---: | ---: | --- |
| One module and one leaf | 3 | 26,094 | Exact prepared file hashes |
| Repeated module with a separate gauge leaf | 4 | 35,450 | Exact prepared file hashes |

The workers use only the SHA-256-verified disclosed neutral requests.
A guard permits exclusive destination writes and directory bookkeeping
during the call. It blocks opening input files or starting external processes.
Sixteen fresh processes cover two successful writes and fourteen refusals.
The two successful results retain native transfer accounting for every
inferred source capability and report both native usability flags false.
Refusals exercise staged failure, late publish denial, a late peer collision,
preflight path and file conflicts, active configuration mismatch, overwrite,
stream transport, unmeasured policy and normal writer selection. A denied
final publish removes the directories created for the call. A concurrently
created companion remains byte-identical and earlier linked files disappear.
[Exact publication receipt](../measurements/2026/SdkNestedAssemblyPublication01.json) ·
[Earlier direct preparation](../measurements/2026/SdkNestedNeutralComposition01.json)

Run the bounded host measurement with the two disclosed neutral recipe
directories available. Its result includes only hashes, counts and diagnostics.

```sh
python3.14 -I -B re/tooling/sw2026/nested_publication/MeasureNestedPublication.py --workspace /path/to/disclosed/workspace
```

Separately, four guarded invocations of the existing flat registry probe
compared the parent revision with this change. The three-occurrence planar
and two-occurrence perpendicular outputs, write results and reader identity
matched exactly on both repetitions. The two parent hashes were
`e4aed259112b5c70796a86772778fa52d57f94381fca9c6b19f828c2aeda8acc` and
`f6a8306cbfb1d5ddc9e6ed832c4fa4959916d9ca936d28742d38a57b2f6dc32f`.
The compact flat receipt digest was
`02ed25ebf622848405b692ba26de1e361af515b3865e6078d3a6aac7f8da42dc`.
The shared child hash was
`352bd2cdae944796307b8e51b667f85dc8ad18551f40b926a7bd870279db6259`.
[Existing flat process probe](../../tooling/sw2026/PublicAssemblyRegistryProcess.py)

## Public activation boundary

Once the corresponding staged outputs pass the native and held-out gates,
extend the assembly branch of `SldprtWriter.supports` with
`CanWriteNested`. Dispatch the admitted nested shape to `EmitNestedMut`
from the assembly write branch before `EmitAsmMut`, which continues owning
the flat profile. Attach the revision-bound usability attestation to the
qualified nested result before returning it to the registry. The existing
registry and transaction already transport the complete sibling set.
The normal discovery registry still contains only its existing SOLIDWORKS
adapter, and its current selection rejects the nested shapes.
