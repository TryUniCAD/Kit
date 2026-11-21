# Cold revolves require each live angle owner

An ordinary single-end revolve allocates one angular display, handle,
dimension and parameter. An ordinary Two Directions revolve allocates
two of each. The older cold geometry check expected one of each class
and rejected a complete Two Directions archive as detached geometry.

Require the allocated inventory to equal the actual `f18` and `f20`
display chains by object identity. A repeated map entry, a missing owner
and a replacement object with the same fields all refuse. The ordinary
root, support, atom and cache checks still apply.

[Guarded cold and malformed contrasts](../../../../../../re/solidworks/measurements/2026/SdkOrdinaryRevolveEndRead01.json)
