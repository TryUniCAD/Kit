# SOLIDWORKS null dispatch arguments need their COM type

The dynamic `SelectByID2` call refused a plain Python `None` for its callout on SOLIDWORKS 2026 SP04.1.
The encoder control authoring phase reported a COM type mismatch at argument eight and saved no part.

For principal planes, retrieve the feature by name and select it through `Select2`.
For calls that require a null dispatch object, pass a `VT_DISPATCH` variant with a null value.
The [round-trip observer](../../../../../re/tooling/sw2026/ObserveEncoderRoundTrip.py) uses a typed null for the save export argument.
