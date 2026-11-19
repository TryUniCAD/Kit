# Parasolid current-schema receive chain links, 2026

This checkpoint proves that the current-schema decoder and scalar-reference fixup preserve the assigned topology links at that boundary. It does **not** yet prove that the entire partition receive/application load leaves those links unchanged before `PK_BODY_ask_edges` or `PK_BODY_ask_faces`.

Task `B04-SW2026-KERNEL-RECEIVE-CHAINS` is owned by `configuration_header`, delivered for PR #121. Root owns native execution and publication. The exact owners/ranges and hashes are in [the source ledger](ParasolidReceiveChainLinks2026.json), with [a source-only receipt](../measurements/2026/ParasolidReceiveChainSource01.json). No native process or hidden source was used in this follow-up.

The work follows the [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [RE playbook](../../Playbook/README.md) and its loader analysis phase. It extends the already frozen [body traversal proof](ParasolidBodyTraversal2026.md) and [partition receive map](PartitionReceive2026.md) without modifying either packet.

## Exact authorities and route

The licensed original `PSKERNEL.dll` is version **37.01.250**, 72,681,488 bytes, SHA256 `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`. The original `sldgciParau.dll` is SHA256 `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`. Neither binary nor a decompiled listing is included.

The bridge at `gciPartition_w::restore` `0x3305ad80` calls `PK_PARTITION_receive` at `0x3305aea7`, through delay thunk `0x330a3313` / IAT `0x3312bf78`. The kernel API entry is `0x1803a80a0`, whose active core call is `0x1803a885f` to `0x1808c86e0`. That core calls DS start at `0x1808c9494`, node receive at `0x1808c95f0`, and DS commit at `0x1808cbeff`.

The current header `SCH_3701250_37102_13006` selects the ordinary node decoder `0x180a26a90`. The schema parser at `0x180a17960` writes the second `SCH_` integer at `0x180a17b06`. That value reaches the start caller's schema output through `0x180a219d9`. The native current-schema leaf `0x18143e4b0` returns **37102**. The alternate node decoder requires the received revision to be strictly newer, plus additional state/mode/capability conditions. At equal revisions, the comparison at `0x180a1c7da` branches to `0x180a1c7de` and clears selector `state+c` at `0x180a1c7f9`.

## Typed field and reference rule

Independent decoding of the five straight-line field registrations confirms all **14** selected links are scalar `p` fields: pointer flag 1, array selector 0 and runtime slot width 8. These are original registration facts, not values fitted to a saved body.

| Class | Runtime fields |
| --- | --- |
| BODY, kind 12 | `owner+b8`, `region+100`, `edge+108` |
| REGION, kind 19 | `next+18`, `shell+28`, `body+10` |
| SHELL, kind 13 | `next+18`, `face+20`, `edge+28`, `region+38` |
| FACE, kind 14 | `next+48`, `shell+60` |
| EDGE, kind 16 | `next+60`, `owner+80` |

The normal field decoder computes the destination from the registered runtime offset (`0x180a25c44`, or matching mapped descriptor `0x180a25c9e`) and calls `0x180a1e210`. Its `p` branch starts at `0x180a1e8fd`: it writes the decoded reference ID into that destination, then advances the runtime slot by 8. It does not insert the referenced entity into a new list.

The later per-node pass `0x180a22d40` visits pointer descriptors with stride `0x30`. It adds the descriptor's runtime offset to the actual node at `0x180a22ded`, reads the saved ID at `0x180a22e31`, resolves that ID through one of the receive maps, and writes the resulting node pointer back to the **same** slot at `0x180a22e5c`. Zero becomes null at `0x180a230e7`. The ordinary pointer map helper `0x181e21ef0` uses a paged direct integer lookup.

A valid compatible reference such as `SHELL.face = transmitted-face-X` becomes a pointer to that same received face X. The `0x180a22f29` branch can clear incompatible targets.

## What remains open

The observed BODY/SHELL/REGION/FACE/EDGE arms of the supplied post-decode callback collect counters and tolerances and inspect self-owner and region validity. Their chain slots remain intact across the observed instructions. One body compatibility branch initializes byte `+c1`. Earlier category branches and later helpers remain to be traced.

After the node receive returns, core `0x1808c86e0` still runs compatibility/normalization work before and after commit. Its complete code interval is `0x1808c86e0..0x1808cdcbd`. A post-commit example calls `ensure_body_meshes` at `0x1808cc0d6` to `0x1808d08f0`. Identifying that mesh path does not exclude every possible analytic-topology side effect elsewhere. No blanket “receive never canonicalizes” rule is established here.

The immediate SOLIDWORKS restore bridge copies the received partition tag, may apply deltas, then enumerates bodies. The rest of SOLIDWORKS load and rebuild behavior needs its own trace. Prior warning-32 cache probes only observed the rebuilt geometry after load failed.

The existing L1/A13/A14 offline inspection covers **three save contexts of one rectangular shape**, with exact partition re-emission and source-predicted chain order different from record order and first face-fin encounters. It is corroboration of the encoded graph, not a new live kernel receive/order measurement.

## Smallest next observation

On one already healthy disclosed ordinary control, the root-owned COM oracle can compare the actual WORLD/body chain after the matching node receive at `0x1808c95f5` with the same body at successful partition return or at the edge/face array fill before tag conversion. Preserve input bytes and avoid deliberate rebuild. Bind the exact module, owned process, receive frame, body pointer, typed owners/backlinks and delivered stops. A changed sequence proves later normalization on that path. Equality qualifies the measured source alone. Track runtime pointers, tags, permanent node IDs, downstream IDs and transmit indices by their actual owners.

No new runtime probe is included or executed. No writer/public behavior or supported coverage changed. The inherited Hopper cleanup is left untouched, and this follow-up starts no REA/Hopper target.

## Source pin verification

[The verifier](../../tooling/sw2026/drawing_edges/VerifyReceiveChainEvidence.py) reads the exact licensed originals and source ledger, validates the full module and every retained code interval hash, and emits only numeric/hash metadata. It does not execute the vendor code and cannot establish native acceptance.

```sh
python3 re/tooling/sw2026/drawing_edges/VerifyReceiveChainEvidence.py \
  --kernel /licensed/path/PSKERNEL.dll \
  --bridge /licensed/path/sldgciParau.dll \
  --record re/solidworks/records/ParasolidReceiveChainLinks2026.json \
  --output /unused/path/ReceiveSourceVerification.json
```
