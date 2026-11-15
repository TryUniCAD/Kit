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

Statistically, the second byte equals `+0x34 & 0xff` for **62 of 68** three-byte prefixes and the
leading byte is the value's high byte with bit 7 set. So the prefix is an encoding of the same
per-class number the registration descriptor carries at slot 0x28 and the registrant exposes at
`+0x34` — not a digest and not set-derived.

## What is left

The prefix and the tail. Hooking `0x1801445xx` during a `SaveAs` and logging the two blocks and the
table read would give them directly, the same way the xxh32 detour gave the name digest.

## Limits

## Limits

- `Writer.py` still requires a retained native document, and the class table is still carried.
- The name digest, the 2-5 byte prefix and the tail are not derived, so no table can be emitted.
