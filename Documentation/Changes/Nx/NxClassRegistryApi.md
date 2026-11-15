# The class registry maps a name to a small integer, not to a hash

## Behaviour

No writer behaviour changed. This records what the vendor module's own symbol table says about the
class registry, which reframes the class-table problem.

## What was measured

`libpart.dll` registers classes by calling an imported constructor:

```text
import libsyss.dll
  ??0ClassRegistrant@OM@UGS@@QEAA@PEBDI...   ClassRegistrant(char const*, unsigned int, ...)
called from 0x1801447d9 with the descriptor built at 0x180144723
```

`libsyss.dll`'s export table then names the registry API directly:

```text
?Name2ClassId@ClassRegistrant@OM@UGS@@SAHPEBD@Z         int   Name2ClassId(char const*)
?Name2Class@ClassRegistrant@OM@UGS@@SAPEAVClass@23@PEBD@Z
?GetClassId@ClassRegistrant@OM@UGS@@QEBAHXZ             int   GetClassId()
?GetClassDigest@ClassRegistrant@OM@UGS@@QEBAIXZ        uint  GetClassDigest()
?EvaluateClassDigest@ClassRegistrant@OM@UGS@@QEAAXXZ
?GetNumClasses@ClassRegistrant@OM@UGS@@SAHXZ
?IsValidClassId@ClassRegistrant@OM@UGS@@SA_NH@Z
?ClassId2Name@ClassRegistrant@OM@UGS@@SAPEBDH@Z
?GetSerialNumber@ClassRegistrant@OM@UGS@@SAHXZ
```

so a class is identified by a **32 bit integer** assigned by the registry (`GetClassId`, `IsValidClassId`,
`ClassId2Name`), with a separate 32 bit digest and a serial number. There is no 71-80 bit hash in the
API at all.

## What this means for the class table

The 71-80 bit "value" in the file's class table was my own reading: the entry is a sequence of five to
nine base-128 fields and I had been concatenating them into one integer. The API says the identifiers
are small integers, so the entry is a record of several small fields — class id, digest, counts —
not a single large hashed value.

That explains, after the fact, why 22 derivations of "name -> one big value" all failed: there is no
such value. The table is a serialisation of small registry fields, and the class id in it is assigned
by registration order at load rather than computed from the name.

## Limits

- The field layout inside an entry is not yet assigned; this entry only says the values are small.
- The registry's id assignment order has not been reproduced.
- `Writer.py` still requires a retained native document.
