# One total angle for symmetric revolutions

Set `AngularRevolve.SideMode` to `symmetric_full` when one feature-owned
parameter controls the entire centred sweep. Put its ID in
`AlongParameterId` and leave `AgainstParameterId` empty. The parameter is
a finite positive angle in radians. A total angle `a` evaluates to
`[-a / 2, +a / 2]` around the effective axis.

Existing `symmetric` features retain their two distinct, equal positive
half-angle parameters. `two_sided` retains independent positive parameters.
`one_sided` retains its signed single driver. The document mapping and JSON
formats use the same fields for all four modes. Adapter-specific support
continues to follow each adapter's documented scope.

The measured SOLIDWORKS 2026 Mid Plane feature has a single total D1 and a
null secondary slot. A fresh SDK process checked neutral JSON readback,
all four span modes and rejection of a second driver or invalid total for
`symmetric_full`. [Native end-owner measurements](https://github.com/TryUniCAD/Kit/blob/b18caa86c15d2c65ad95c9a572bbc9d06701da8c/re/solidworks/measurements/2026/RevolveEndOwners01.json)
