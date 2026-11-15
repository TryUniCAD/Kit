# The modern type registry is a token grammar, not a captured table

The modern SPLMSSTR type registry was the last blocker for authoring a part from scratch. It is now
fully decoded from the shipped bytes and the cadmpeg open specification, and the per-class values
are proven to be class constants rather than loader-session values.

## Behaviour

`ClassTable.ReadRegistry` parses the three regions of a modern type registry in declaration order:

```text
reference list: <declared_len:u8><name[declared_len-1]><code:u8> ... 01
class region:   <declared_len:u8><name[declared_len-1]>
                <storage:token><base:token><schema_fingerprint[8]><reference:token> ... 02
member region:  <declared_len:u8><name[declared_len-1]><storage:token><owner:token> ...
```

A registry token is a variable-width integer:

```text
direct  = value:u8                    # 00..7f
compact = prefix:u8, low:u8           # 80..8f, value = (prefix-80)*256 + low + 1
wide    = prefix:u8, value:u16 BE     # 90, a0..af, f1, value = ((prefix&0f)*65536) + value + 1
null    = ff
```

`declared_len` counts the name plus the first registry byte after it, so the name is
`declared_len - 1` bytes. The class region ends with `02` or with one opaque separator byte before
the member region; `ReadClasses` accepts both.

## The class region is the inheritance graph

`base` is the one-based ordinal of the parent class in the same region, and `0` denotes the root.
Measured on `wave_modern.prt`, all 160 classes have an in-range base and every base names a class
whose name is a prefix of the child or shares its schema. The chain is therefore derivable from the
registry alone.

`schema_fingerprint` is the eight bytes already decoded as the name digest (first four) and the
layout digest (last four). `reference` is a one-based ordinal into the reference list.

## The per-class storage code is a class constant

The `storage` token was the suspected session value. It is not. Three parts written by the same NX
2506 installation agree on every shared class:

```text
part             classes  shared with wave  storage match  fingerprint match
wave_modern.prt      160                  -              -                  -
flange_modern.prt    252                103            103                103
fresh_block.prt      154                149            149                149
```

`fresh_block.prt` is a part created from scratch by a journal, not migrated from a legacy file, so
the agreement is not an artifact of migration. The storage code is a property of the class, not of
the document or the session.

## Verification

`TestNxClassTable` builds a synthetic registry with a reference list, two classes and one member,
and asserts every field, the compact and wide token decodes, and the null token. The parser was run
against the three corpus parts:

```text
part             references  classes  members
wave_modern.prt          82      160        9
flange_modern.prt       118      252       14
fresh_block.prt          79      154       10
```

## Limits

The member region is parsed leniently: it stops at the first declaration that does not fit the
`<name><storage><owner>` shape, because the field registry is followed by the object-id table and
entity records. The storage code is a class constant but is not yet derived from the vendor binary;
a from-scratch writer still needs a class-to-storage table, which is format knowledge rather than
donor data. The class region end marker is `02` in some parts and an opaque separator in others.
