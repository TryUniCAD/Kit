# Drawing sheet dimensions round through different owners

The native Definition stores the sheet width and height as binary doubles. The
properties stream also describes the paper with decimal text. These two
representations can differ by one floating-point unit for the same physical
sheet. An ANSI A sheet read through the strict Definition path yielded height
`0.21589999999999998 m`. The existing partial XML path reported `0.2159 m`.

Keep the actual Definition value in a strict document. Check geometric
agreement across representations and compare serialized bytes within each
owner. Converting the XML text back to a double and substituting it in the
Definition changes the source value. Both CLI writer routes and the strict
readback are exercised in the same process-boundary check.
[Strict reader scope](../../../../../Reference/Research/Solidworks/Reading/GeneratedBlankStrictReader.md)
