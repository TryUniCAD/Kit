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

## The class entry carries the registry's class digest

The entry layout resolves once the live registry's per-class digest is used as an anchor. For every
class whose `GetClassDigest` is nonzero, the digest's four bytes appear **verbatim** inside the
stored entry:

```text
classes with a nonzero digest                        135
digest found verbatim in that class's entry          135 of 135
digest offset within the entry                       6, 7, 8 or 9 (varies with the prefix length)
```

so an entry is

```text
<prefix, 6-9 bytes> <class digest, 4 bytes little-endian> <tail, 1-2 bytes>

UGS::RM_part              32f71f03be4   25 5a 70 c8   01      digest 0xc8705a25
UGS::Sketch::Colors       f474de4695f   c5 3f 28 d7   01      digest 0xd7283fc5
UGS::Solid::Body          1efb4308a48   bb 21 1c 01   06      digest 0x011c21bb
UGS::POINT                6100001df8e17 4a b9 d4 b5   09      digest 0xb5d4b94a
```

The prefix decodes as one big-endian base-128 integer of 36 to 63 bits, and the tail as a small
integer. Neither matches the registry's class id, attribute count, superclass id or the `+0x34`
dword — 0 relations across the 135 classes:

```text
prefix - id / attrs / superclass / +0x34      135 distinct values each
tail == id 0/135   tail == attrs 3/135   tail == superclass 1/135
```

The 19 classes with a zero digest (for example `UGS::OM::RootObject`) carry no digest field at all,
which is why their entries are shorter and why their windows never matched.

## The digest is schema-derived, and not from the attribute names alone

The class schema can be enumerated at runtime through `Class::GetAttributeCount`,
`Class::GetAttribute(index)` and `Attribute::GetName`, which makes the digest testable:

```text
class                    digest      flat attributes
UGS::OM::RootObject      00000000    34
UGS::RM_part             c8705a25    32
UGS::POINT               b5d4b94a    36
UGS::OM::ObjectState     c7e30705    12
UGS::Sketch::Colors      d7283fc5    33
UGS::Solid::Body         011c21bb    40
```

Nine digest functions over the attribute-name lists — xxh32 at seeds 0/1/2, crc32, adler32, md5
truncated little and big, sha1 truncated, blake2b-4 — across six separators, forward and reversed
order, with and without the class name, in both latin-1 and UTF-16LE, match **none** of the five
classes. So the digest covers more than the attribute names: types, sizes, offsets and flags are in
the schema too, and `Attribute` exposes those as `GetType`, `GetSize`, `GetOffset`, `GetRTL`,
`GetDimensions`.

## The digest is supplied at registration, not computed by the registrant

The class schema is now dumped per attribute — name, type, size, offset, alignment, properties,
RTC, class id and attribute id — for 153 classes, and refitting the digest over that data fails too:

```text
field sets     name, name+type+size, name+type+size+offset, type+size+offset,
               type+size+offset+props, ids, name+ids, text form
separators     none, NUL, pipe, semicolon
digests        xxh32 (seed 0, 1), crc32, fnv1a-32, md5 (little and big), blake2b-4
classes        135 with a nonzero digest
matches        0 for every combination
```

so the digest is not a hash of the attribute records either. Reading the code instead of fitting it:
`ClassRegistrant`'s constructor at `0x180069fd0` stores the field from **its own argument**:

```text
0x18006a0be  mov eax, dword ptr [rbp + 0x380]
0x18006a0df  mov dword ptr [r13 + 0xb0], eax
```

`[rbp + 0x380]` is a stack argument slot in the constructor's frame, so the value arrives from the
caller. The constructor does not compute it. The registration call site in `libpart.dll` builds the
argument list next to the descriptor:

```text
0x1801447cf  lea rdx, [rip + 0xa30f3a]     parent name
0x1801447d6  mov rcx, rbx                  this
0x1801447d9  call qword ptr [ClassRegistrant constructor]
             mov dword ptr [rsp + 0x28], 0x80000111
             mov dword ptr [rsp + 0x30], 0x21000
```

which means the digest is a **compile-time constant carried by the registering module** and passed
in, rather than something the loader derives. That is the first evidence that the class table can be
recovered statically: each class's digest should sit, as a literal, at that class's registration
site.

## The digest is extractable from the modules by scanning registration sites

The digest is a compile-time immediate. Every registration site contains

```text
c7 84 24 90 00 00 00 <digest LE>     mov dword ptr [rsp + 0x90], <digest>
```

immediately before the call that constructs the registrant, and the class name is the `rdx` value
of that call. Scanning `libpart.dll` and `libsyss.dll` for that pattern and resolving the `rdx`
`lea` against `.rdata` produces 590 `(name, digest)` pairs. Checked against the 135 digests read
from a live registry:

```text
pairs extracted                                    590
pairs that match the live registry                  35
pairs that disagree with the live registry           0
classes not present in the two modules scanned      100
```

Adding `libmodl.dll`, `libmodlgeom.dll` and `libmodlint.dll` raises the extraction to 1,084 pairs
and still yields **0 mismatches and the same 35 agreements**, because those modules do not contain
the registration sites for the classes that were missing. Following the class name directly is no
help either: `UGS::Solid::Body`, `UGS::POINT` and `UGS::LAYER_category` have **no `lea` xref at all**
in the five modules inspected, so their names reach the registrant through a pointer table rather
than a direct `lea`, which is a different registration shape from the 35 that do match.

**zero mismatches** across every pair that could be checked. The 100 misses are classes registered
by modules that were not copied to the host (`Solid::*`, `UGS::POINT`, `LAYER_category`, and so on),
not failures of the rule.

So the class digest is not a runtime value at all: it is a constant compiled into the module that
registers the class, and the rule that recovers it is

```text
find mov dword [rsp+0x90], imm
follow forward to the next call
take the string loaded into rdx  ->  class name
take imm                        ->  class digest
```

That means the digest field of the class table is **statically derivable from vendor code** — not a
document, not a live session — which is the first part of the table that is.

## Registration is concentrated in modules that import the registrant constructor

Anchoring on the import rather than on the name string settles where classes are registered. Of the
modules inspected, only two import `ClassRegistrant`'s constructor at all:

```text
libpart.dll       imports ??0ClassRegistrant@OM@UGS@@QEAA@PE...   (one IAT slot)
libmodlint.dll    imports it                                      (one IAT slot)
libsyss.dll       does not import it — it defines it
libmodl.dll       does not import it
libmodlgeom.dll   does not import it
pskernel.dll      does not import it
```

`libmodl.dll` and `libmodlgeom.dll` only import class-id globals such as
`?ThisClassId@BaseDimension@Annot@UGS@@2AEAHEA`, so they consume identifiers rather than register
classes. That is why none of the classes missing from the extraction appear there.

`libmodlint.dll` does import the constructor, but its three `UGS::Solid::Body` references are not
registrations: the surrounding block registers handlers under names like `UGS::DPLANE`,
`UGS::BCURVE` and `UGS::FEATURE_RECORD` in a lookup table, which is a different table from the class
registry. So a name string appearing next to class machinery does not imply a registration.

Searching the installation for the constructor's import name shows dozens of modules importing it
(`camservices.dll`, `libadvpbcore.dll`, `libaecdesign*.dll`, `libaerostruct*.dll`, …), so the
remaining 100 digests are registered by modules that are not on this host. Closing them means
copying the registering modules, which is a build-time extraction over the installed product rather
than a runtime dependency.

## What this means for a static writer

The entry is a snapshot of **registry-derived per-class values**, one of which is the class digest.
The digest is not a hash of the name: 30 digest functions over 10 name encodings do not produce it.
What remains is that it is a digest of the class's _schema_ — its attribute list — which the registry
builds when each module registers its classes with `AddAttribute`.

Reproducing that statically therefore needs two things, in order:

1. the registry's attribute names for a class, from `?GetAttribute@Class@OM@UGS@@QEBAPEAVAttribute@23@H`
   and `Name2AttributeId`, so the schema can be enumerated at runtime and the digest function fitted
2. the same schema from static data, since each module's `AddAttribute` calls pass literal name
   strings that live in `.rdata` next to the call sites

## Limits

- The entry's field positions are not assigned to registry properties.
- Because ids are load-order serial numbers, a table emitted from any source other than a live registry
  would be correct only for the exact module set that produced it.

- The field layout inside an entry is not yet assigned; this entry only says the values are small.
- The registry's id assignment order has not been reproduced.
- `Writer.py` still requires a retained native document.
