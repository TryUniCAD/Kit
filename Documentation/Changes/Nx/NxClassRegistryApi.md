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

## No field behaves like a sequential class id

With the registry API known, the 129 entries were split into their base-128 fields and each field
index was tested for the shape a class id would have — small, and unique:

```text
field 0   129 values   16 below 256    89 distinct   min 4            max 531,946,195,134,471
field 1   129 values   89 below 256    94 distinct   min 4            max 5,731,327,779
field 2   129 values   75 below 256   106 distinct   min 1            max 761,326,338,412,426,118
field 3   124 values   68 below 256   109 distinct   min 0            max 65,389,423,389,631
```

no field is small-and-unique across the table, so the class id is not carried as a bare integer in a
fixed position. The sequences mix small counts with values in the 2^20 and 2^30 ranges, which is what a
serialised record of mixed properties looks like:

```text
UGS::OM::RootObject            56, 100, 9648, 56917797, 15606, 2
UGS::RM_part                   101, 103, 10143784975, 90, 112, 200
UGS::OM::SaveAuditTrail        1713280, 96, 396820, 106, 1068840, 1
UGS::Sketch::Colors            1651715, 111, 10513, 1041119, 40, 343
```

assigning those positions to the registry's properties needs the stores in
`??0ClassRegistrant@OM@UGS@@QEAA@PEBDI...` at `0x180069fd0` matched against the serialiser, which is
the next step and was not completed.

## The class id is a runtime serial number, not a derived value

Three accessors settle where the identifiers come from, read from the export table:

```text
?GetSerialNumber@ClassRegistrant@OM@UGS@@SAHXZ
  0x18006e1c0  mov eax, dword ptr [rip + 0x682396]   ; a global counter
  0x18006e1c7  ret

?GetClassId@ClassRegistrant@OM@UGS@@QEBAHXZ
  0x18003b0a0  mov rax, qword ptr [rcx + 0x28]       ; pointer to an int
  0x18003b0a4  mov eax, dword ptr [rax]
  0x18003b0a6  ret

?GetClassDigest@ClassRegistrant@OM@UGS@@QEBAIXZ
  0x18003b090  mov eax, dword ptr [rcx + 0xb0]       ; a per registrant dword
  0x18003b096  ret
```

so an id is stored in a table pointed to from the registrant, a digest is a dword at `+0xb0`, and the
registry keeps a **global serial counter**. Class ids are therefore assigned **at load, in registration
order**, not computed from the name. That is the definitive answer to why 22 name-derived functions
failed: the value is not a function of the name at all.

It also means a class table cannot be produced by static analysis of the modules. Reproducing it needs
the registration order of 1,178 class names spread across several modules, which is a property of a
running NX session rather than of the binaries.

## The entry framing is not plain base-128

Walking the table by name lengths exposes a contradiction with the field reading used so far. The
first entry's bytes are

```text
14  "UGS::OM::RootObject"  38 74 b0 4b a5 fe 91 1b f6 79 02  0d "UGS::RM_part" ...
                            ^^ first entry byte, high bit clear
```

so `0x38` terminates a base-128 value, which would make the entry a one-byte value of 56 followed by
unrelated bytes. That cannot be right, because the same bytes decode to the six field sequence
`56, 100, 9648, 56917797, 15606, 2` under the loader used for every earlier measurement.

The name length byte is also one greater than the name: `0x14` is 20 for a 19 character name. So the
entry's framing has at least one convention I have not identified, and every field-level conclusion in
this document inherits that uncertainty. Recording it here rather than building on it.

## The registry is callable at runtime, and its values are not in the table

The registry can be queried from a journal in a running NX through `ctypes` and `GetProcAddress`
on the decorated export names. This is a measurement of the kernel's own API, not a copy of any
document:

```text
libsyss.dll module base         resolved
?Name2ClassId                   resolved
?GetNumClasses  ->  7806
?GetSerialNumber ->  7804
UGS::OM::RootObject      ->  91
UGS::OM::RootObjectGroup ->   2
UGS::RM_part             ->  2715
UGS::POINT               ->  4492
UGS::Sketch::Colors      ->  2743
UGS::NotAClass           -> 65535   (invalid)
```

`Name2Registrant` then exposes per class the attribute count, the superclass id and the digest
dword at `+0xb0`, so the registry's whole view of a class is readable.

That makes the decisive comparison possible: query the registry for all **154** names in
`dim40.prt`'s table and look for each value inside that class's stored entry.

```text
classes queried                                 154
entries searched                                all
id found inside its entry, any of le1/le2/le3/le4/be1/be2/be3/be4/base-128    0
field matches against id / digest / attribute count / superclass id            0
```

So the table is **not** a copy of the registry's identifiers, digests, attribute counts or
superclass links. The values are computed by the loader from something not exposed by these
accessors, which is why no field lines up and why the entry is stable across parts with the same
class set.

Combined with the swap test (see `NxClassTableScope.md`), the conclusion is that a class table can
only be produced by the loader that validates it. It cannot be derived from names, permuted between
classes, copied from the registry, or shared between class sets.

## Limits

- The entry's field positions are not assigned to registry properties.
- Because ids are load-order serial numbers, a table emitted from any source other than a live registry
  would be correct only for the exact module set that produced it.

- The field layout inside an entry is not yet assigned; this entry only says the values are small.
- The registry's id assignment order has not been reproduced.
- `Writer.py` still requires a retained native document.
