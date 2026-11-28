# Generated document precision does not replace the dual setting

Both generated SOLIDWORKS parts kept the same native dual linear precision. The document-table setting changed the independently measured primary linear, angular, mass, force, energy, power and time preferences from four places to two. The complete `GetUnits` array also retained the generated fraction denominator even when the reported decimal places agreed with the independent stock.

Capture named native preferences as well as `GetUnits` and distinguish applicable formatting from stored inactive fields. A native length-only API setter is a separate contrast. [Native evidence](../../../../re/solidworks/records/VendorBlindBossNativeUnitPrecisionProof.json) · [SOLIDWORKS unit preference reference](https://help.solidworks.com/2025/english/api/swconst/dp_units.htm?format=P&value=)
