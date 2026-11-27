# Saved SOLIDWORKS sketch evidence starts inside the class entry

## Expectation

A native profile owner and a typed sketch can cite the same reader span and native identity.
The common span can appear to locate the whole class entry or the inner sketch object.

## Actual behavior

Four P01 and P03 source checks found the profile class entry at byte 5,554, the common reader span at byte 5,578, and the inner sketch at byte 5,771.
The source archive parser tracks the separate profile and inner sketch objects.
The common span corroborates the reported ownership. It does not delimit either native object.

## Workaround

Use the [typed profile reader](../../../../src/convert/adapters/solidworks/Resolved/ProfileSketch.py) for exact class and inner sketch boundaries.
Use the [comparison observation](../../../Changes/Research/Encoder/NativeSketchOwnership.md) only to relate records with the same reader evidence.
