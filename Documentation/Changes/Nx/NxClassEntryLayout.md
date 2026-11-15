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

## The prefix and the tail

Those two fields remain unidentified.

## Limits

## Limits

- `Writer.py` still requires a retained native document, and the class table is still carried.
- The name digest, the 2-5 byte prefix and the tail are not derived, so no table can be emitted.
