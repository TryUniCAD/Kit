# SOLIDWORKS 2026 archive object and class tags

This record establishes the structural tag grammar from the pinned 2026 native implementation. It does not establish descriptors, map contents, feature schemas, fresh-model construction, or native acceptance.

## Scope and identity

- Module: `swccu.dll`, version `34.5.2.0604`, preferred base `0x31a30000`.
- Full module SHA-256: `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c`.
- Licensed image and existing decompile remain outside the checkout under `Sw2026Research01a1dc84`.
- Evidence: existing private 2026 decompilation, independently checked original instructions with LLVM, and original PE exception data. No saved CAD streams were read.
- PE exception directory: RVA `0x3a000`, size `11748`, exactly `979` twelve-byte records. Extents below include chained fragments, not raw `.pdata` padding.
- [Reverification](../v2026/Reverification.md) and [archive-map construction](ArchiveMapConstruction2026.md) provide the enclosing 2026 context. No 2025 function address or assumed rule was admitted.

The accompanying [metadata](ArchiveTagGrammar2026.json) contains fragment identities and instruction-window hashes without vendor instruction listings.

## Complete native functions

All intervals are half-open. Span hashes cover original bytes in the pinned image, including every contiguous chained fragment.

| Native owner               | Complete extent           | Bytes | Fragments | SHA-256                                                            |
| -------------------------- | ------------------------- | ----: | --------: | ------------------------------------------------------------------ |
| `su_CArchive::ReadClass`   | `[0x31a3a2d0,0x31a3a54e)` |   638 |         1 | `4cc3a859c6f80bd33917528ca84cd7a09befa24cd1b3a7ca9a1b797e7c546393` |
| `su_CArchive::ReadObject`  | `[0x31a3a550,0x31a3a781)` |   561 |         5 | `f0df2c866475589522468bc63e508763695e34eec607a77975cc8b723c6ae43d` |
| `su_CArchive::WriteClass`  | `[0x31a3a850,0x31a3a92e)` |   222 |         5 | `3f669130b07f70d233357904c8bc35f268d00f671a8443bd714ef67c5482da0f` |
| `su_CArchive::WriteObject` | `[0x31a3a930,0x31a3aac8)` |   408 |         1 | `474c25ccadca80f9def23e1803ac567387dbe37e4e7ceff6a30d2ddb67a723ad` |
| `su_CArchive::MapObject`   | `[0x31a3a110,0x31a3a2c9)` |   441 |         1 | `15fe96b3db13ac6d65ca43438193932a4f517e029525b00f859e77492350d505` |
| Allocation-limit helper    | `[0x31a39d60,0x31a39d8a)` |    42 |         1 | `e7ec26797981e629d3e7bb0533be0cc4c89591bea60a42a15877c8d1edd83e40` |

## Read grammar and branch order

Let `S` be the first little-endian u16. Only `S=0x7fff` consumes an additional little-endian u32 `L`.

For every other `S`, native normalization computes:

`L = ((S & 0x8000) << 16) | (S & 0x7fff)`.

The initial u16 and normalized u32 remain distinct until the new-class check. `ReadClass` performs the short/escape selection at `0x31a3a316–0x31a3a353`, tests the normalized sign at `0x31a3a357–0x31a3a359`, and tests the **original u16** against `0xffff` at `0x31a3a382–0x31a3a385`.

| Condition                                                 | Structural result                             |            Bytes consumed by tag primitive |
| --------------------------------------------------------- | --------------------------------------------- | -----------------------------------------: |
| `S=0xffff`                                                | New class; descriptor belongs to higher layer |                                          2 |
| `S=0`, or escaped `L=0`                                   | Null object                                   |                                     2 or 6 |
| Class bit clear, `L>0`                                    | Object reference with index `L`               |                                     2 or 6 |
| Class bit set, `L & 0x7fffffff > 0`, original `S!=0xffff` | Class reference with index `L & 0x7fffffff`   |                                     2 or 6 |
| Class bit set, index zero                                 | Invalid class reference                       |                    2 or 6 before rejection |
| Incomplete u16 or selected u32                            | Incomplete tag, rejected by the memory reader | Available bytes only; no successful result |

`ReadClass` masks and explicitly rejects zero class index at `0x31a3a438–0x31a3a43e`, then checks it against the current load array at `0x31a3a444–0x31a3a451`. That membership check requires archive state and remains outside the primitive.

The nonclass branch of `ReadClass` returns its normalized integer through the supplied object-tag output. Direct class-only use without that output is rejected at `0x31a3a35b–0x31a3a35e`; the general tag parser does not impersonate that contextual API.

`MapObject` initializes the load array to one element and writes null into slot zero at `0x31a3a233–0x31a3a24b`. `ReadObject` validates the object index and retrieves that slot at `0x31a3a58a–0x31a3a5ae`. Consequently, escaped zero reaches the same null slot as short zero. Null normalization is a structural rule, not a saved null value.

## Write grammar

For a resolved positive reference index `I`, native store uses the following bit-width formulas. Addition of the class bit is equivalent to bitwise OR because the admitted index cannot contain that bit.

| Kind             | Condition                   | Computed encoding                          |
| ---------------- | --------------------------- | ------------------------------------------ |
| Null             | Structural null             | `u16(0)`                                   |
| New class        | Unregistered runtime class  | `u16(0xffff)` then higher-layer descriptor |
| Object reference | `1 <= I < 0x7fff`           | `u16(I)`                                   |
| Object reference | `0x7fff <= I <= 0x7fffffff` | `u16(0x7fff), u32(I)`                      |
| Class reference  | `1 <= I < 0x7fff`           | `u16(I + 0x8000)`                          |
| Class reference  | `0x7fff <= I <= 0x7fffffff` | `u16(0x7fff), u32(I + 0x80000000)`         |

`WriteClass` uses the unsigned threshold and class-bit writes at `0x31a3a88e–0x31a3a8d4`; its new-class marker is at `0x31a3a8d9–0x31a3a8de`. `WriteObject` selects null at `0x31a3a9a6–0x31a3a9bf`, and its unsigned width threshold and escaped object write occur at `0x31a3a9d9–0x31a3aa16`.

The short escape itself occupies index `0x7fff`; compact class `0xffff` is the new-class marker. Both reference kinds therefore switch at the same strict `<0x7fff` boundary. Escaped payload `0x0000ffff` remains object reference `65535`; escaped `0x80007fff` remains class reference `32767`; escaped `0xffffffff` is class reference index `0x7fffffff`. These examples are computed consequences of the branch grammar.

## Domain and map ownership

The tag payload reserves one class bit, leaving unsigned reference index domain `1..0x7fffffff`; zero is reserved for structural null in the object namespace and rejected in the class namespace. Negative integers, booleans masquerading as integers, and indices beyond this domain cannot be encoded by the typed primitive.

This wire domain does not assert that every such index can exist in a native map. The allocation helper compares the current counter with `0x3ffffffe` at `0x31a39d64–0x31a39d6b` and rejects greater-or-equal counters. Native fresh allocation therefore admits a next index only while `counter < 0x3ffffffe`. The shared primitive neither allocates nor synthesizes that map.

Null and references do not allocate entries. A new class descriptor and a new object allocate independently in the shared namespace. The caller must preserve the entire map and counter context described in [archive-map construction](ArchiveMapConstruction2026.md), including linked configuration dependencies. No feature-count formula or semantic default is introduced.

## Noncanonical forms and source boundary

Native read accepts an escaped small reference; native write selects the compact form. The typed value retains kind and index, not original width. Arbitrary overlong byte identity is therefore not claimed.

The existing research `Core.read_class` already canonicalizes reference widths on store, but it labels escaped object zero as `objref(0)` rather than structural null. The new reader follows native null-slot semantics. Parent integration must route actual read/write paths through the primitive and retain contextual missing-reference, schema, and descriptor failures.

The typed files perform no file I/O, vendor loading, CAD execution, donor lookup, offset patching, or captured-value replay. New-class names and schema numbers are deliberately absent; structural marker coverage does not supply descriptor semantics.

These formulas apply when the enclosing native API actually reads a tag. `ReadObject` tests archive flag `0x10` at `this+0x20` in `0x31a3a557–0x31a3a56b` and returns null without consuming input when it is set. `ReadClass` rejects a supplied expected runtime class whose schema field equals `0xffff` at `0x31a3a2f9–0x31a3a301`, before tag reading. Neither contextual early exit is implemented as fabricated tag bytes. Archive mode and expected-class policy remain higher-layer responsibilities.

## Evidence and unfinished work

High-confidence static evidence closes tag grammar, unsigned width selection, zero-class rejection, null-slot normalization, and full native owner extents. It does not close runtime class identity, map type ownership, class descriptor domains, all archive contexts, generated feature values, or parametric construction.

Only static source review, AST parsing, and formatting have been performed on this draft. No codec execution, local tests, native CAD files, held-out payloads, VM, application, services, or licenses were accessed. Current-source integration and remote real archive CLI process checks are pending; no native acceptance is transferred from earlier revisions.

The required [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), full [instruction book](../../Playbook/README.md), and [loader chapter](../../Playbook/LoaderAnalysis.md) apply. The criteria's stopping conditions are:

> The first is success under every criterion on this page.

> The second is the end of the available context.

> Missing grammar is the work. It is not a blocker.

YOU DO NOT HAVE THE ORACLE. DO NOT LAUNCH, ATTACH TO, OR AUTOMATE THE CAD APPLICATION. REQUEST MEASUREMENTS FROM THE ORACLE OWNER.
