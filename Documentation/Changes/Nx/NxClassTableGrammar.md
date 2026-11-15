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

## The storage code is the registration class id plus one

The storage code is not a document value and not a session value. It is the class's registration id
in the vendor binary, stored one-based so that zero can mean "no class".

`UGS::OM::ClassRegistrant::ClassRegistrant` in `libsyss.dll` takes the class name, a class id, a
schema array, a `CustomProperties` block, a `ClassAttributeStruct`, three constructor callbacks and
the layout digest. The registration sites in `libpart.dll` and `libsyss.dll` are the
`c7 84 24 90 00 00 00 <layout_digest>` stores that precede that call.

Matching the 160 class names of `wave_modern.prt` against the registration sites of the two shipped
libraries gives 20 classes. For 19 of them exactly one constructor stack argument equals
`storage - 1`, and in all 19 it is the argument at `[rsp + 0x40]`:

```text
class                          storage  argument  argument + 1
UGS::BaseTypes::ExtendedObject     101       100           101
UGS::SO                           201       200           201
UGS::ES_base_parameter            502       501           502
UGS::RM_int_record_area           901       900           901
```

The twentieth match, `UGS::ES_base_parameter`, has no such argument inside the captured window; that
is a window-extraction artifact, not a counterexample, because the same class matches at another
site. The rule is therefore `storage = registration_class_id + 1`, and a from-scratch writer can
obtain it from the vendor's own registration sites instead of from a captured document table.

## Limits

The member region is parsed leniently: it stops at the first declaration that does not fit the
`<name><storage><owner>` shape, because the field registry is followed by the object-id table and
entity records. The class region end marker is `02` in some parts and an opaque separator in others.
The storage derivation is measured on 20 of the 160 classes; the remaining 140 are registered in
libraries that are not part of the shipped corpus, so the rule is confirmed but not exhaustively
enumerated.
