# Fresh prism edge registration order, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID`; owner `/root/assembly_occurrence`; delivery PR #121. Root owns generated edge operands, component/reference wrappers, shared integration and the native oracle. This tranche closes the bounded `f380` hash-growth and list-order derivation for a fresh ordinary prism supplied twelve allocated IDs `7..18`. It does not add edge wrappers or claim a complete accepted downstream cache.

The exact fresh store order is **`7,8,9,10,11,12,13,14,15,16,17,18`**. The edge table grows from eight to sixty-four buckets before inserting ID `15`. This conclusion follows actual insertion, rehash and serializer branches, not a signed numeric sort. [Numeric source pins](DownstreamEdgeRegistrationOrder2026.json) · [Process receipt](../measurements/2026/DownstreamEdgeRegistrationOrder01.json) · [Existing face ownership](DownstreamFaceRegistration2026.md)

## Source identity and separate table ownership

Every address below belongs to original `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, 46,536,280 bytes, preferred base `0x4b140000`, build `34.5.2.0604`. Scope is ordinary archive version `19000`. Nine complete functions, nineteen instruction windows, three imported scalar primitives and six numeric constants are reproducibly pinned. The bucket-vector assignment includes all five chained unwind fragments. The separate load-reserve helper is a complete 283-byte leaf without unwind metadata; it ends at its own return. No vendor instruction listing is included.

Downstream construction calls the same table initializer separately for `f340` and `f380` at `0x4b51d59f` and `0x4b51d5ac`. Initializer `0x4b2dc240` creates a distinct circular list sentinel and zero count, mask `7`, bucket count `8`, maximum load factor binary32 `1.0`, and sixteen bucket-boundary cells. A face table's occupied buckets never seed the edge table.

Bucket-vector assignment `0x4b27f510` receives that actual sentinel as its fill value. Its fresh allocation branch explicitly fills every cell with the supplied pointer (`0x4b27f5ec..0x4b27f60c`). The same routine initializes the new bucket vector during rehash, so an empty bucket is established by source, not by guessed zero pointers.

Type selection in `0x4b5293d0` maps face code `0x138c` to `+0x340` and edge code `0x138a` to `+0x380`. Both selected tables then use **the same** insertion function `0x4b51a800` at call `0x4b5295b9`. The current serializers use different key scalar overloads: `f340` uses `unsigned int`, while `f380` uses Windows signed `long`, both 32 bits. The edge count also uses signed `long`. These primitive choices do not introduce signed-key ordering into the runtime hash table.

Insertion hashes the four little-endian key bytes, each explicitly zero-extended. FNV-1a uses offset basis `0xcbf29ce484222325`, prime `0x100000001b3` and modulo `2^64` multiplication. Lookup uses `hash & mask`, then exact 32-bit key equality. No signed less-than comparison sorts these entries. The loader's separate unsigned nonzero-key test is retained in the [archive grammar](DownstreamIdArchiveGrammar2026.md); it does not turn zero/tombstone rows into ordinary fresh identities.

## Growth happens before the new node is linked

Insertion computes binary32 `(old_count+1)/bucket_count`. It skips growth when the maximum load is at least that value. The count and bucket conversions include unsigned-64 high-bit handling; every integer and result in this bounded twelve-entry member is exactly representable. The tool refuses a larger profile rather than pretending that its small-integer calculation proves the entire large-table domain.

When the limit is exceeded, the source computes the minimum bucket count as `ceil(prospective_count/max_load)`, at least eight. For old bucket counts below `512`, it selects eight times the old bucket count if that meets the minimum. Rehash helper `0x4b4c84b0` rounds the requested count to a power of two, installs the corresponding mask and rebuilds the bucket boundaries.

For the ninth entry, prospective count is `9`, old buckets `8`, binary32 load `1.125`, minimum `9` and selected request `64`. Rehash produces exactly sixty-four buckets and mask `63`. The pending key was already hashed, but the insertion function recomputes its bucket and insertion position after rehash at `0x4b51aa1c`; it does not retain the old colliding bucket's insertion position.

Rehash traverses the prior list with a saved next pointer. An empty destination bucket only sets its boundary pair and performs no list splice (`0x4b4c858f..0x4b4c85a0`). All eight retained prism keys reach that branch. The rehash collision/splice branches are pinned but are not admitted by this numeric constructor.

| Allocated ID | Bucket under mask 7 | Bucket under mask 63 |
| -----------: | ------------------: | -------------------: |
|            7 |                   2 |                    2 |
|            8 |                   5 |                   61 |
|            9 |                   4 |                   44 |
|           10 |                   7 |                   31 |
|           11 |                   6 |                   14 |
|           12 |                   1 |                   57 |
|           13 |                   0 |                   40 |
|           14 |                   3 |                   27 |
|           15 |                   2 |                   10 |
|           16 |                   5 |                    5 |
|           17 |                   4 |                   52 |
|           18 |                   7 |                   39 |

IDs `7..14` occupy eight distinct original buckets. ID `15` initially searches old bucket two, which contains ID `7`, then triggers growth before linkage. Its new bucket ten is empty. The remaining new buckets for IDs `16..18` are empty too. Thus every actual insertion uses the before-sentinel branch and appends to the forward list; the temporary old-bucket collision does not become an occupied-bucket insertion.

The serializer reads edge count at `+0x390`, obtains the sentinel at `+0x388`, starts at `sentinel.next`, writes each key and conditional actual `uniqueIdInfo_c` pointer, then advances through `node.next` (`0x4b520170..0x4b5201e0`). It does not iterate bucket numbers. That establishes the exact order above without relying on the keys happening to be ascending.

## A native-loaded table has a different preparation path

The existing read branch clears the table and reserves using the incoming count before reconstructing rows. Leaf `0x4b5370b0..0x4b5371cb` selects the required capacity and tail-jumps to the same rehash helper. For incoming count twelve and maximum load one, it requests twelve, which rounds to sixteen buckets. It does not replay incremental eight-to-sixty-four fresh growth. Buckets are not serialized, so a correct fresh table need not reproduce a loaded table's runtime capacity.

The twelve key hashes are also distinct under mask fifteen, so the supplied ordinary twelve-key sequence remains collision-free after this separate reserve. This is a static distinction, not a native reload or save result. Do not use a saved table's capacity as a fresh-constructor rule.

## Reproducible bounded numeric proof

[CheckEdgeRegistrationOrder.py](../../tooling/sw2026/downstream/CheckEdgeRegistrationOrder.py) verifies the original module, complete functions, scalar imports and numeric constants through the existing PE verifier. It then consumes only authored integer keys and `wire_type` from stdin. Its independent byte-based FNV calculation agrees with the shift-based calculation; a circular linked-list model follows the exact empty-bucket insertion and rehash branches. Output is numeric JSON evidence, not a native CAD file or downstream body.

```sh
printf '%s\n' '{"keys":[7,8,9,10,11,12,13,14,15,16,17,18],"wire_type":"i32"}' |
  uv run --no-project --offline --isolated --python 3.11 python -B \
  re/tooling/sw2026/downstream/CheckEdgeRegistrationOrder.py \
  --root /absolute/Kit \
  --model /absolute/licensed-originals/sldmodu.dll \
  --record re/solidworks/records/DownstreamEdgeRegistrationOrder2026.json \
  --output /unused/EdgeMapOrder.json
```

The output file must be absent. Two fresh signed-prism processes must produce identical receipts; an unsigned-key process must reproduce the same key bits, hashes, bucket history and list order. The six-face control `1..6` retains its existing eight-bucket allocation order. The receipt binds the actual positive and refusal results, formatting and source identities. No model file, native payload, VM, COM or Hopper session is used.

Admission is deliberately bounded: at most twelve unique nonzero 32-bit wire keys, with no actual rehash collision or occupied final insertion bucket. A transient old bucket collision resolved by growth is allowed and recorded. Duplicate/update behavior, general collision-group ordering, larger counts, other release implementations, body/edge identity construction, native cache acceptance and held-out generalization remain outside this tranche. Signed-bit numeric probes do not qualify negative IDs as authored CAD identities. Existing writer operands and every earlier frozen packet remain unchanged.
