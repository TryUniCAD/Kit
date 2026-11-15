# The vendor class registry is in libpart.dll and the ids are not stored

## Behaviour

No writer behaviour changed. This records where NX keeps its class names, which decides how the
class table could ever be emitted.

## What was measured

Class names are not in `pskernel.dll`: neither `UGS::OM::RootObject` in ASCII or UTF-16, nor the
encoded id bytes of `RootObject`, `RM_part` or `POINT`, occur in its 72,362,496 bytes. A search
across the NX installation finds the full names in several modules, and the copy inspected locally is

```text
libpart.dll   22,599,008 bytes   contains UGS::OM::RootObject at 0xb75398
```

the string sits in a registry entry, followed by eight zero bytes and then four eight byte pointers:

```text
55 47 53 3a 3a 4f 4d 3a 3a 52 6f 6f 74 4f 62 6a 65 63 74   UGS::OM::RootObject
47 72 6f 75 70 00 ...                                       Group\0
78 3f de 80 01 00 00 00   70 69 36 80 01 00 00 00
00 ee 32 80 01 00 00 00   d8 69 b7 80 01 00 00 00
```

so the registry name is `UGS::OM::RootObjectGroup`, and the file's table carries the shorter
`UGS::OM::RootObject`: the two are related but not identical strings.

Twenty of the first forty table names occur in `libpart.dll`, and for none of them does the class id
appear in any encoding — eight byte, ten byte, four byte low word, or the original base-128 bytes:

```text
names found                   20 of 40
id found as 8 byte LE          0
id found as 10 byte LE         0
id found as base-128 blob      0
id found as 4 byte low word    0
```

## What this means

the ids are **computed at runtime**, not stored: the registry holds names and pointers, and the
71-80 bit value is produced by code. That is why twenty-two derivations from the names alone failed —
the function is in the module's code, not in its data, and reading it needs a disassembler rather
than a string or byte search.

## Limits

- No disassembly was performed, so the function is still unread.
- The name mismatch (`RootObject` against `RootObjectGroup`) is recorded but not explained.
- `Writer.py` still requires a retained native document.
