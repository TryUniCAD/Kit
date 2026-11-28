# SOLIDWORKS receipt integers can exceed floating-point range

Python JSON can represent an integer that cannot convert to a finite floating-point observation.
Comparisons against infinity accept such an integer before conversion raises `OverflowError`.
This caused out-of-range volume and centre values to escape the normal receipt refusal.

Convert each receipt scalar to a finite float before testing its sign.
Reject values outside that range as an invalid measurement before publishing.
The [publication check](../../../../../re/solidworks/EncoderBoundary/CheckQualifiedPublication.py) verifies this outcome through both SDK writer entry points.
