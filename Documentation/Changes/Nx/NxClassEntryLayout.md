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

## The name digest

The name digest is computed at load: it is not stored anywhere in the modules, appearing as bytes
for only 2 of 152 classes and never near the class name. With 152 `(name, digest)` pairs available,
these functions are excluded:

```text
xxh32 seeds 0-16      murmur3-32 seeds 0-4     java 31-hash
crc32 (and final-xor variant)                  xxh64 low and high halves, seeds 0-4
```

so the name digest is still underived. The prefix and the tail are the other two unknown fields.

## Limits

- `Writer.py` still requires a retained native document, and the class table is still carried.
- The name digest, the 2-5 byte prefix and the tail are not derived, so no table can be emitted.
