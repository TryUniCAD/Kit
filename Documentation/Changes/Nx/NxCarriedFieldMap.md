# Which bytes of the carried view and instance records are free

## Behaviour

No writer behaviour changed. This records a field classification for the two families the
census left, so a later emitter knows which bytes it may choose.

## What was measured

Single byte flips in `dim40.prt`'s 27 byte `02 02 41 5b` instance records and `empty.prt`'s
83 byte `02 02 41 41` view records, each loaded in NX 2506:

```text
27 byte instance record
  offset 4   flip    OPEN_FAILED
  offset 8   flip    OPEN_FAILED
  offset 12  flip    loads       bodies 1  volume 23999.999999999996
  offset 13  flip    loads       bodies 1  volume 23999.999999999996
  last byte  flip    loads       bodies 1  volume 23999.999999999996

83 byte view record
  offset 4   flip    OPEN_FAILED
  offset 8   flip    OPEN_FAILED
  offset 12  flip    OPEN_FAILED
  offset 41  flip    loads       bodies 0
  last byte  flip    loads       bodies 0
```

so each family has a validated frame in its first thirteen bytes and free bytes after it: the
instance records are free from offset 12, the view records from somewhere between 13 and 41, which
is consistent with the earlier finding that a view's matrix and extents are not revalidated.

## A free single byte does not license a free region

Three rewrites of the 27 byte `02 02 41 5b` instance records were tried after the single byte flips
above, each loaded in NX 2506:

```text
tail bytes 21..25 set to 01 in all six records      OPEN_FAILED
tail bytes 21..25 set to 01 in one record           OPEN_FAILED
class marker 12..13 set to 80 86 in all six         OPEN_FAILED
```

So single byte flips that load say less than they appear to: the bytes I flipped individually are
either redundant or their new value happened to be acceptable, while any deliberate rewrite of the
region is refused. The family therefore stays carried, and the earlier note that it is "free from
offset 12" is withdrawn — that conclusion came from one-byte flips and does not generalise.

This is a methodological caution worth keeping: in this format, a byte that survives a single flip
is not thereby a field the writer may choose.

## Multi-byte rewrites confirm both families are validated

The caution above says a single-byte flip proves nothing. Applying multi-byte rewrites to the 83
byte `02 02 41 41` view records instead:

```text
matrix region 26..76 replaced with a different eight byte word, both records   OPEN_FAILED
name token L2 -> L9, same length, both records                                  loads   bodies 0
last four bytes zeroed, both records                                            OPEN_FAILED
```

so the view's matrix is validated against the record as a whole — the single-byte flips that loaded
earlier changed bytes whose values are redundant until the matrix as a whole is consistent — and the
only field the writer may choose is the name, which `RenameView` already supports.

Both remaining carried families are therefore validated: the instance records refuse a tail or
marker rewrite, the view records refuse a matrix rewrite, and neither yields a field that can be
generated. Section 0's emission has reached its ceiling by this method:

```text
body-less part  346-347 differing bytes of 33,395-33,407
body part       362 differing bytes of 36,694
```

raising it further needs either the semantics of these validated values or the class table, not more
mutation.

## The REA retry, with the file on the host

`pskernel.dll` was copied out of the NX 2506 installation inside the virtual machine to the host
(`re/nx/oracle/pskernel.dll`, 72,362,496 bytes), on the theory that REA could not read a file that
only existed inside the VM. Opening it still fails:

```text
provider   hopper
operation  close_binary
cleanup    incomplete
issues     authenticated shutdown acknowledgement was not observed
           private runtime retained (runtime root /tmp/rea-*)
```

so the blocker is the Hopper provider's lifetime, not the file's location. REA has not produced a
single successful open in this work, and that earlier hypothesis is now refuted.

## Limits

- Two families, five flips each; the exact boundary of the view record's free region is between
  offsets 13 and 41 and is not pinned down.
- Nothing is emitted for either family, so section 0's differing-byte count is unchanged at
  346/347 for a body-less part and 362 for a body part.
