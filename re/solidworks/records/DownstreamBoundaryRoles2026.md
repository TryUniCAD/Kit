# Conditional downstream boundary roles in SOLIDWORKS 2026

This is a source-only checkpoint. It proves the conditional role assignment and attribute domains in the pinned implementation; it does not qualify a generated drawing or final native edge-reference state.

Task `B04-SW2026-DOWNSTREAM-BOUNDARY-ROLES`, owner `configuration_header`, delivery PR #121. The exit for this slice is a reproducible original-module check and a bounded model-derived role recipe. Root owns integration, product execution, and native acceptance. All CAD inputs and held-outs remained unopened in this slice.

## Evidence and build

The numeric [record](DownstreamBoundaryRoles2026.json) and [source-verification receipt](../measurements/2026/DownstreamBoundaryRoleSource01.json) bind complete function fragments, typed imports, vocabulary and the narrower instruction intervals. The complete original module hashes are:

| Module | SHA256 |
| --- | --- |
| `PSKERNEL.dll` | `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969` |
| `sldgciParau.dll` | `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |

The host verified 61 complete function entries and 108 source intervals. Eight imports are bound by the exact original images; two include independently identified kernel delay thunks. The retained private disassembly is not part of this packet. Native runs, SDK product executions, CAD input reads, VM calls, and Hopper/REA target opens were all zero.

This extends [fresh reference assignments](DownstreamFreshReferenceAssignments2026.md). Its frozen source record remains `40c9215a5c71105ee20235d1f2da106c913e6fe1f0f69f1ad42c4d88150437a7`. No predecessor artifact was changed.

## Three different edge attribute domains

The ordinary `moCoEdge` helper at `0x4be81690` first resolves the actual coedge's edge. With special ID manager `0x4db5dd18` absent, it calls `moEdge::getEdgeId` at `0x4be81700`. That function queries `gcEdgeIdAttrib_w::getOldestFromEntity`, obtains the returned attribute's actual representation and assigns it to the target `moEntityId` through `0x4c6cee50`.

The Parasolid implementation at `0x32fa2990` selects **`edgePermId_ad`**, global `0x3312d718`. The initializer constructs it from `EDGE_PERM_ID_2001` at `0x32f9dff1`/`0x32f9e0f0`, retains it in R14 and publishes it at `0x32f9e319`. Its retired vocabulary is `EDGE_PERM_ID`.

| Vocabulary | Actual global | Meaning for this rule |
| --- | --- | --- |
| `EDGE_PERM_ID_2001` | `0x3312d718` | The permanent-edge attribute queried by the boundary and own-edge lookups |
| `EDGE_ID_2001` | `0x3312d720` | Separate sketch/entity pointer definition, published at `0x32f9ef70` |
| `DOWNSTREAM_EDGE_ID` | `0x3312d550` | The allocated downstream attribute, published at `0x32fa0948` |

These are different native definitions. Neither an existing downstream ID nor a sketch pointer attribute proves a successful permanent-edge lookup.

The helper at `0x32fa37b0` returns null when the selected permanent-attribute count is zero (`0x32fa37c9..0x32fa37e0`). A single attribute is returned through the single-attribute path. The multi-attribute and environment-dependent representation branches are retained in the numeric ranges but are not proposed as a new generative rule.

The model helper tests whether the attribute is nonnull; it does not add a second nonnull-representation test before reporting success. A corrupt or unrepresented permanent attribute must not be turned into the face-fallback branch by an invented rule.

## Actual role selection

Let `c` be the actual coedge selected by the already-proved ordinary edge factory. For a classic normal edge with a nonnull curve and exactly two live loop-owned opposite-sense fins, this is the unique positive fin, including line and circle curves. It is not unconditionally the transmitted `EDGE.halfedge`.

| Role key | ID slot | Source of the actual face or alternative |
| --- | --- | --- |
| 0 | 0 | `face(c)` |
| 1 | 1 | `face(other(c))` |
| 2 | 2 | First look up the permanent ID of `edge(previous(c))`; on failure use `face(other(previous(c)))` |
| 3 | 3 | First look up the permanent ID of `edge(next(c))`; on failure use `face(other(next(c)))` |

The previous-edge lookup is at `0x4b75ab44`. Its successful branch skips both the surface fallback and key-2 insertion; failure reaches the actual start face and insertion at `0x4b75ab7e`. The next-edge lookup is at `0x4b75aba4`, with key-3 fallback insertion at `0x4b75abdf`.

On a successful boundary lookup, the ID slot holds the actual permanent-edge representation and the corresponding `f10` face role is absent. This is an alternative semantic representation, not an edge's allocated downstream row ID placed in a face slot.

The current edge has an independent presence test at `0x4b75a968`. It chooses four or five ID slots. If present, the current edge's permanent representation goes into slot 4 at `0x4b75aa08`. No `f10` role 4 is inserted by these paths.

`previous` and `next` follow the actual loop. The backend calls `PK_FIN_ask_previous_in_loop` and `PK_FIN_ask_next_in_loop`. Their ordinary plain-world cores load `HALFEDGE.backward` at `+0x20` (`0x1803132bd`) and `HALFEDGE.forward` at `+0x18` (`0x18031222d`). Those offsets match the independent runtime field registration. They are not geometric endpoint sorting or edge-array predecessor/successor rules.

## Fresh order and attachment

The orchestrator builds face rows before edge rows. For each edge, it:

1. Constructs the actual component/reference and its role data at `0x4b52ad43`; the failed first validation can reconstruct mode 0 at `0x4b52ae1c`.
2. Allocates the shared counter and appends `f60` at `0x4b52ae4a..0x4b52ae8c`.
3. Appends the actual edge to `f6e8` and installs its `f4c0` row index at `0x4b52ae8c..0x4b52aed8`.
4. Calls unique-info registration at `0x4b52af07`. Its edge branch reaches `0x4b52f420`, which selects that actual edge and calls `gcEdge::setDownstreamId` at `0x4b52f626` when the cached identity has not already matched.
5. Performs post-insert validation, which can replace the reference pointer while retaining the allocated row ID, and then advances to the next edge at `0x4b52b062..0x4b52b081`.

The Parasolid setter at `0x32f953b0` selects `downstreamEdgeId_ad`, not `edgePermId_ad` or `edgeId_ad`. Its fresh branch creates the downstream attribute at `0x32f954d3`; reuse/update paths are separate. Thus earlier edge-row attachment cannot make the start/end permanent lookup succeed. The later `0x4b5360d0` pass is not the first attachment point for all downstream edge IDs.

## Bounded deterministic recipe

For a freshly authored prism or cylinder graph, this role-only recipe applies when all of the following are explicitly true:

- The ordinary nonmesh helper branch has usable model surface-ID context, active downstream scope, and no special global ID manager.
- Participating edges have nonnull curves and exactly two live loop-owned opposite-sense fins.
- Current, previous and next actual edges have no `EDGE_PERM_ID_2001` in the generated graph.
- Every selected face resolves through the actual `f48` face-to-index map to a nonzero allocated ID.

Select the unique positive live fin. Compute keys 0, 1, 2 and 3 from the four face expressions above, retain equal IDs under different keys, and emit the map in ascending signed-key order. The four ID slots hold the actual corresponding face representations. No optional own-edge slot 4 exists in this scoped case.

No face ID comes from a kernel node ID, transmit index, atom ID or feature ID. A missing face or zero allocation does not authorize an invented ID. The native insertion helper skips a missing/zero face; a stricter complete generated writer should refuse an unexpected missing dependency.

When a real loop contains one fin, `previous(c) == next(c) == c`. With no permanent edge IDs, keys 2 and 3 therefore equal key 1. Distinct role keys must be retained. This is a graph consequence and does not assert that every cylinder uses that topology.

## Ambiguity and unresolved scope

The initial validator at `0x4b525960` checks actual common-edge topology of the role-0/1 faces. If exactly two common edges are reported, `0x4b525aca..0x4b525b0a` requires role-2 and role-3 faces different from both adjacent faces to accept the mode-1 trial. A self-loop case whose fallback roles equal key 1 cannot satisfy that branch; the caller retries mode 0. Post-insert validation may also replace a reference without allocating a new row ID.

This packet does not derive those later cache/ambiguity/anti-copy/vertex-hint fields. It also does not generate a nonempty permanent-edge attribute, qualify multiple permanent attributes, establish the special manager or `0x4b7555d0` fallback, or widen to wire, laminar, mesh, nonmanifold and special kernel-world/body modes. Final reference state and native end-to-end acceptance remain separate work.

The first missing dependency for the permanent-ID alternative is a proved model-derived `EDGE_PERM_ID_2001` representation and its environment-specific materialization. The strict no-permanent-ID branch does not require that representation and must not invent it.

## Reproduction

Run [VerifyBoundaryRoleSources.py](../../tooling/sw2026/downstream/VerifyBoundaryRoleSources.py) with `--bin-directory` for the licensed original modules, `--kernel` for the pinned original kernel, `--record` for this JSON record and a new `--output`. The verifier hashes original files and numeric intervals only. It does not execute vendor code or parse a CAD file.

Read the [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and [RE playbook](../../Playbook/README.md) before advancing the construction or native qualification.
