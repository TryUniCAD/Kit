# The class table entry is a prefix, two digests and a tail

## Behaviour

No writer behaviour changed. This entry records that the section-0 class table is now decoded
except for one field, which changes what a class-table emitter would have to compute.

## The layout

Every entry is

```text
<prefix, 2-5 bytes> <name digest, 4 bytes LE> <layout digest, 4 bytes LE> <tail, 1 byte>
```

and both digests come from exported registry API functions:

```text
?OM_get_class_name_digest@@YAIPEAVClass@OM@UGS@@@Z            unsigned int OM_get_class_name_digest(Class*)
?OM_get_class_layout_digest@@YAIPEAVClass@OM@UGS@@_N@Z        unsigned int OM_get_class_layout_digest(Class*, bool)
```

Measured against the live registry and the file:

```text
UGS::OM::RootObject   38 74 | b0 4b a5 fe | 91 1b f6 79 | 02
                      prefix| name fea54bb0| layout 79f61b91| tail
UGS::RM_part          65 77 | 8f c0 f7 e4 | 25 5a 70 c8 | 01
                             | name e4f7c08f| layout c8705a25|
UGS::Solid::Body      3d 7b | 21 c2 14 c8 | bb 21 1c 01 | 06
                             | name c814c221| layout 011c21bb|
UGS::POINT       83 84 80 80 | 0e 7e 9c 17 | 4a b9 d4 b5 | 09
                             | name 179c7e0e| layout b5d4b94a|
```

Verifying over the whole table: **152 of 154** entries contain their class's
`name digest || layout digest` consecutively, and the tail is **one byte in all 152**. The two
failures are `UGS::Facet::JT::Body` and `UGS::Facet::JT::BodyLOD`, which the session's registry does
not know.

Prefix lengths across the table: 2 bytes (19), 3 (68), 4 (51), 5 (14).

## What this fixes in the earlier record

The field I had called "the digest" is the **layout** digest, and it is the constant written at the
class's registration site, which is why it is extractable statically (90 of 135 classes, 0
mismatches). The 4 bytes I had been reading as "prefix" are in fact the **name** digest, so the
earlier claim that the prefix moves by `S(set) * 2^28` described the low bytes of the _name_ digest
and is superseded: what moves with the class set is the remaining 2-5 byte field, not the name
digest.

## The name digest is xxh32 over a schema name, a class name and one dword

Reading `OM_get_class_name_digest` at RVA `0x107030` identifies the algorithm outright. The
function builds the xxh32 accumulator set from the published primes and then finalises it:

```text
mov dword ptr [rsp + 0x28], 0x24234428     acc1 = PRIME1 + PRIME2      (seed 0)
mov dword ptr [rsp + 0x2c], 0x85ebca77     acc2 = PRIME2
mov dword ptr [rsp + 0x30], 0             acc3 = seed
mov dword ptr [rsp + 0x34], 0x61c8864f     acc4 = -PRIME1
...
rol ecx, 1 ; rol eax, 7 ; add ; rol 0xc ; rol 0x12     the xxh32 merge
add ecx, 0x165667b1                        PRIME5 for the short-input path
```

Those four constants are exactly xxh32's initial state at seed 0, and the fallback addition is
`PRIME5`, so the function is stock xxh32. `HashXxh` in Kit reproduces it: `xxh32("")` is
`0x02cc5d05`, which is why so many classes carry the layout digest `0x02cc5d05` — their layout is
empty.

The input is built by the feeder at RVA `0x1095f0`, which hashes three things in order:

```text
schema name   the string behind  Class* -> [inner + 0x28]
class name    the string behind  Class* -> [class + 0x48]
dword         [inner + 0x40]
```

read at runtime with `0x10bef0` as the string accessor and `0x66c40` as the inner accessor:

```text
class                    schema name            class name              dword   stored digest
UGS::OM::RootObject      UGS::OM::Meta          UGS::OM::RootObject        1      fea54bb0
UGS::RM_part             UGS::RM                UGS::RM_part            0x2f      e4f7c08f
UGS::POINT               UGS::POINT             UGS::POINT              0x40      179c7e0e
UGS::Solid::Body         UGS::Solid::Topol      UGS::Solid::Body        0x19      c814c221
UGS::Sketch::Colors      UGS::Sketch::Colors    UGS::Sketch::Colors      0x05      d7283fc5
```

48 hand-built variations of that triple reproduced none of the stored digests, because the triple is
emitted **once per inheritance link**, not once per class. Hooking the update routine at RVA
`0xe97d0` (patch the entry to a `ctypes` callback that records `(data, length)` and returns) and
calling `OM_get_class_name_digest` shows the exact stream:

```text
UGS::OM::RootObject   "UGS::OM::Meta" "UGS::OM::MethodicObject" 01000000
                      "UGS::OM::Meta" "UGS::OM::StorableObject" 01000000
                      "UGS::OM::Meta" "UGS::OM::TaggedObject"   01000000
                      "UGS::OM::Meta" "UGS::OM::RootObject"     01000000

UGS::POINT            ... "UGS::OM::VersionedObject" 01000000
                      "UGS::RM" "UGS::RM_entity"            2f000000
                      "UGS::RM" "UGS::RM_displayable_entity" 2f000000
                      "UGS::SO" "UGS::SO"                   12000000
                      "UGS::POINT" "UGS::POINT"             40000000
```

so the digest is

```text
nameDigest = xxh32( for each link of the inheritance chain, root-most first:
                        schema(link) ++ class(link) ++ u32(link) )
```

and `xxh32(stream)` reproduces the stored digest for **152 of 152** classes.

`ClassEntry.NameDigest(Links)` implements it and `ClassEntry.EntryParts(Entry, Digest)` splits an
entry into prefix, layout digest and tail. `TestNxClassLink` pins three chains to their measured
digests and checks the split of a real entry.

## The entry writer is located

`OM_get_class_name_digest` has exactly one caller in `libsyss.dll`, and it sits 16 bytes from the
only caller of `OM_get_class_layout_digest` that shares a function:

```text
0x1801446ca  call 0x180107030    OM_get_class_name_digest
0x1801446cf  mov r15d, eax
0x1801446d2  mov [rbp + 0x48], eax
0x1801446d5  xor edx, edx
0x1801446d7  mov rcx, r13
0x1801446da  call 0x180106f90    OM_get_class_layout_digest
0x1801446df  mov r14d, eax
```

so the routine at `0x1801445xx` is the **class-table entry writer**, and the surrounding stores show
the entry's byte order:

```text
0x18014474e  mov [rcx + rax], r15b        first byte of the name digest
0x18014475e  mov [rdx + rcx + 1], al      second
0x18014476e  mov [rdx + rcx + 2], al      third
0x18014477e  mov [rdx + rcx + 3], al      fourth
0x180144782  add dword [rbx + 0x70], 4    advance the stream cursor
```

immediately before it, a **two byte value is read from a table**, not computed:

```text
0x180144651  mov rdx, [rbx + 0x30]        the table
0x180144655  mov rax, [r13 + 0x30]
0x180144659  movsxd rcx, dword [rax + 0x98]
0x180144660  add rcx, rcx                 index times two
0x180144663  movsx r8d, word [rdx + rcx]  a 16 bit per class value
0x180144668  mov [rbp + 0x48], r8w
```

and earlier in the same routine a four byte block is written from `[rbp + 0x50]` when a flag at
`[rbx + 0x18c] & 4` is clear. That accounts for the prefix being 2 to 5 bytes: the entry carries a
variable-width leading field before the two digests.

The prefix values themselves are consistent with a per-class table entry rather than a computed
digest: `UGS::OM::RootObject` has `0x7438`, `UGS::RM_part` `0x7765` and `UGS::Solid::Body` `0x7b3d`,
which rise with registration order across the table.

## The prefix carries the class's +0x34 value

Decoding the prefix against the descriptor value shows it is a byte string carrying that number, big
endian, with a marker bit set in its leading byte:

```text
part                          prefix            +0x34        reading
UGS::OM::SaveAuditTrail       80 c9 78          201          byte 1 = 0xc9 = 201
UGS::OM::SaveAuditTrailEntry  80 c8 78          200          byte 1 = 0xc8 = 200
UGS::Sketch::Colors           83 e8 74         1000          byte 1 = 0xe8 = 1000 & 0xff
UGS::POINT                    83 84 80 80       900          0x0384 = 900
UGS::SKELETON_grid_modeling   88 34 80 81      2100          0x0834 = 2100
UGS::DWG_member_view_parameter 87 d0 80 83     2000          0x07d0 = 2000
UGS::Attr::DAttributeDescriptionDepository a0 27 10 80 85  10000   0x2710 = 10000
```

Statistically, across the whole table:

```text
prefix length   classes   byte 0 == 0x80 | (r >> 8)   byte 1 == r & 0xff
2                    19              0                        0
3                    68             62                       62
4                    51             39                       39
5                    14              0                        0
```

so for the 119 classes with a 3 or 4 byte prefix, the first two bytes are the class's `+0x34` value
with bit 7 set on the high byte, and the remaining one or two bytes follow. The 33 classes with a 2
or 5 byte prefix do not follow that shape: their leading bytes encode `0x7438`, `0x7765`, `0x7465`
for classes whose `+0x34` values are 55, 100 and 100, so those encode a larger number and the
encoding of the leading field is not settled.

## The tail byte

The tail is one byte in all 152 classes, with values from 1 to 79. These readings are excluded:

```text
attribute count                                    5 of 152
table index                                        2 of 152
ordinal within the class's schema, table order     8 of 152
ordinal within the class's schema, registry id     6 of 152
ordinal within the class's schema, name order      7 of 152
GetCurrentSchemaVersion                            returns -1 for class names
```

The tails cluster per schema — the twelve `UGS::OM::Meta` classes carry 1..12 in some order — so it
is a per-schema ordinal, but the ordering is neither the table order, the registry id nor the name,
and 8 of 152 is far too low to call it derived.

## The `+0x34` value itself

That value is a per-class registry constant with the shape of an enumerated scheme rather than a
size: the classes run `1, 2, 3, 5, 10, 11, 40, 50, 55, 60, 70, 86, 100, 101, 160, 170, 196, 200,
201, 247, 253, 255, 289, 300, ...` up to `58000`, and none of them matches the class's attribute
layout size (max offset plus size is 204 for `UGS::OM::RootObject` against `+0x34` = 55). It is a
descriptor constant, extractable from the same registration sites that already yield the layout
digest.

## The store sites are a generic byte writer, not the entry assembler

Reading the routine that contains those store sites shows it takes its payload from the caller:

```text
0x180144560  push rbp
0x18014456a  movzx edi, word ptr [rbp + 0x48]     length, from the stack
0x180144580  mov rcx, [rbx + 0x60]                stream buffer
0x180144589  movzx eax, byte ptr [rsi]            payload, from rsi
0x1801445ad  mov eax, dword ptr [rsi]             the 4 byte path
0x1801445bc  call 0x18035908e                     memcpy for other lengths
```

so `0x180144560` writes whatever blob the caller hands it in `rsi` with length `[rbp+0x48]`, and the
four byte block at `[rbp+0x50]` and the 16-bit table word are _additional parts the same routine
appends_. That means the prefix's leading bytes are assembled **by the caller** and simply pass
through here — the store sites the plan targets would log bytes that the caller already computed.

## The enclosing routine and its caller

`0x180144560` is not a function entry: the routine that contains it starts at `0x180144100` and has
exactly **one** caller, at `0x180141f63`. Reading from the real entry shows what it does first:

```text
0x180144121  cmp dword ptr [rcx + 0x2c], 0        a count of classes
0x180144131  loop:
0x180144135    mov rcx, qword ptr [rsi + rax]     one class pointer
0x180144161    call 0x180066c40                   the inner accessor
0x180144180    compare and append to a vector at [rbx + 0x300]
0x1801441c9  mov rdi, [rbx + 0x308] - [rbx + 0x300]
0x1801441d7  sar rdi, 3                            divide by eight
0x1801441db  mov [rbp + 0x48], edi                 the collected count
0x180144206  mov [rcx + rax], dil                  first byte of a four byte field
```

so the routine first collects the classes into a vector and writes a **four byte count**, then walks
the entries. The two-byte table read at `0x180144663` and the four byte block at `[rbp + 0x50]` come
later, once per class.

That orders the work: the prefix is produced by the per-class part of this routine, which begins
after `0x180144651`, and the value it stores is read from `[rbx + 0x30]` at an index of
`2 * [[r13 + 0x30] + 0x98]` — a per-session table, not a per-class constant this file can supply.

## The writer hook: installed, fired, and negative

A trampoline was installed on the entry assembler `0x180144100` (copy the `push`/`sub rsp` prologue
into a `VirtualAlloc` page, append an absolute jump back, patch the entry with an absolute jump to a
`ctypes` callback that logs and then calls the thunk) and a `SaveAs` of `dim40.prt` was driven from
the same journal. The hook installed and fired **seven** times with these counts:

```text
9, 15, 17, 24, 30, 52, 157
```

so the routine is a general table writer, and the 157-entry call is the class-set one. But the table
it reads at `[rbx + 0x30]` is **not** the prefix source: sampled at entry it is almost entirely
`0xffff`, with a few small values (`0x8c`, `0x91`), and **zero** of its values match the first two
bytes of any stored entry prefix. It is an allocated-id occupancy map, the same shape as the
occupancy object in the expression section.

So the prefix's 16-bit value is filled into that structure _during_ the routine, after the point
where an entry hook can observe it, or it comes from somewhere else entirely. Reading it needs a
mid-function observation, which is the trampoline problem the entry hook avoided.

## A bounded memory scan of the writer context is also negative

The entry trampoline was hardened: `VirtualQuery` is used to prove a range is committed and readable
before any read, the callback never dereferences a class pointer, and the scan is gated on the
157-entry pass. It then walked every pointer-sized field of the writer context and dumped 1 KiB from
each readable target:

```text
writer invocations logged        7   (counts 52, 15, 157, 30, 17, 9, 24)
memory blocks dumped from the 157 pass   50
stored prefixes found in any of them     0 of 152
```

so the prefix is not present, in its stored form, in any structure the writer context references at
its entry point. It is produced later, or it is derived from a value rather than copied.

## What is left

The prefix and the tail. Hooking `0x1801445xx` during a `SaveAs` and logging the two blocks and the
table read would give them directly, the same way the xxh32 detour gave the name digest.

## Limits

## Limits

- `Writer.py` still requires a retained native document, and the class table is still carried.
- The name digest, the 2-5 byte prefix and the tail are not derived, so no table can be emitted.
