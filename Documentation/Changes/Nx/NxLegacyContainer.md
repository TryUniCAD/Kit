# The legacy container is writable where the modern one is not

## Behaviour

No writer behaviour changed yet. This entry records a measured opening for the from-scratch write
path: the modern `SPLMSSTR` container's class table is mandatory and validated (see
`NxClassTableScope.md`), but NX 2506 also opens the **legacy container**, and that container's class
table carries only data that is derivable from the vendor modules.

## The legacy container is an OLE2 file with the same stream names

Three parts in the corpus are not `SPLMSSTR`:

```text
flange.prt       310784 bytes   d0cf11e0a1b11ae1   OLE2
vise_screw.prt   102912 bytes   d0cf11e0a1b11ae1   OLE2
wave_parent.prt   80384 bytes   d0cf11e0a1b11ae1   OLE2
```

and NX 2506 opens all three, reporting geometry:

```text
FILE flange.prt       bodies 1 volume 75385.62526149699
FILE wave_parent.prt  bodies 1 volume 1000000.0000000002
FILE vise_screw.prt   bodies 1 volume 1.7805678853189086
```

Inside, the stream names match the modern container:

```text
UG_PART/UG_PART           141768   the model
UG_PART/DisplayJT          51816
UG_PART/JT                 22454
UG_PART/ExternalReferences   760
part/attrs                   525
images/preview              7881
qafmetadata                 2359
```

only the payload magic differs: `0d 01 "UGII  " <u32 version>` instead of `SPLMSSTR`. The existing
payload reader returns zero sections for it, so this is a separate container format.

## The legacy class table is the inheritance link plus one constant

At the first class name the bytes are

```text
06 0d 00 "UGS::OM::Meta"        01 00 00 00  13 00 "UGS::OM::RootObject"       37 00 00 00
06 07 00 "UGS::RM"              28 00 00 00  0c 00 "UGS::RM_part"             64 00 00 00
06 0d 00 "UGS::OM::Meta"        01 00 00 00  17 00 "UGS::OM::SaveAuditTrail"   c9 00 00 00
```

so each entry is

```text
0x06 <u16 schema length> <schema name> <u32 schema flag>
     <u16 class  length> <class  name> <u32 value>
```

Parsed over `flange.prt` (233 entries) and `vise_screw.prt` (192 entries):

```text
flange.prt      233 entries, 12198 table bytes, 99 distinct schemas
vise_screw.prt  192 entries,  9771 table bytes
the 4th byte field is constant within every schema      99 of 99
value == the registry's +0x34 for every shared class   127 of 127
```

There is **no name digest, no layout digest, no per-class code and no tail** — the four fields that
made the modern table unemittable. What remains is the schema name, a per-schema constant, the class
name and the `+0x34` value, and that value is the descriptor immediate at the class's registration
site, which is already extractable (slot `0x28`, 90 of 90 sites; see `NxClassRegistryApi.md`).

## Only the class name is validated

The legacy stream is stored in OLE2 sectors, so a same-length edit can be patched into the file
without rewriting the container. Four copies of `flange.prt` were built that way and loaded:

```text
leg_control.prt   byte copy                                           bodies 1  volume 75385.625261497
leg_value.prt     RootObject value 55 -> 54                            bodies 1  volume 75385.625261497
leg_schema.prt    schema UGS::OM::Meta -> UGS::OM::MetX                bodies 1  volume 75385.625261497
leg_rename.prt    class UGS::OM::RootObject -> UGS::OM::RootObjecX     OPEN_FAILED
```

so in this container the **class name is the only validated field**: the `+0x34` value can be altered
and the schema name can be altered, and the part still loads with identical geometry. That is the
opposite of the modern container, where a one-bit change to the per-class code or to the tail is
rejected (see `NxClassTableScope.md`).

For a writer this means the legacy class table can be emitted from the class list alone:

```text
0x06 <u16 len> <schema name> <u32 schema flag> <u16 len> <class name> <u32 value>
```

with the class names being the only values that must be the loader's own, and those are the names of
the classes the part actually uses. The schema names and the `+0x34` values should still be written
correctly — they are registration-site data — but they are no longer a gate.

## The container can be written, and NX accepts it

`re/nx/tools/OleWrite.py` writes an OLE2 file from a stream dictionary: 512 byte sectors, a mini
stream and mini FAT for streams under 4096 bytes, the correct root CLSID, and a directory built as a
balanced tree. Rebuilding every stream of each corpus part through it and loading the result:

```text
part              streams rebuilt   round trip   NX 2506
flange.prt                  17 of 17   identical   bodies 1  volume 75385.625261497
vise_screw.prt               6 of 6    identical   bodies 1  volume 1.7805678853189086
wave_parent.prt              4 of 4    identical   bodies 1  volume 1000000.0000000002
```

The volumes match the originals exactly, so the container layer is written rather than copied: NX
reads our container, our directory and our stream layout. The directory must be a balanced tree;
`Documentation/Gotchas/Conversion/NxLegacyDirectoryTree.md` records that requirement and the
five-entry experiment that isolates it.

What remains for a from-scratch part is the `UGII` payload itself, not the container and not the
class table.

## Limits

- The legacy payload writer is not implemented. This entry establishes the container and the class
  table; the `UGII` payload body is still carried from a source part.
- NX 2506 does not save this container, so no new samples can be generated; the three corpus parts
  are the whole evidence base, and `wave_parent.prt` did not yield the table at the anchor the other
  two use, so its layout differs.
- `Writer.py` still raises for a neutral document. The modern container remains unwritable because
  of the validated class table, and no part has been authored in either container yet: what is
  established here is that the legacy table is not a gate, not that the legacy payload is written.
- `re/nx/examples/` holds these parts; nothing from it is copied into `src/`.
