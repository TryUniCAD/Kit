# Dynamic SOLIDWORKS dispatch results can be callable

A no-argument SOLIDWORKS member can appear as a Python method or as its evaluated value.
A dispatch wrapper for an evaluated value can also report itself as callable.
The first encoder authoring attempt that reached inspection called the wrapper returned by `FirstFeature`.
That call reported `Member not found`. The process exited normally and produced no accepted measurements.

Distinguish a method from a dispatch wrapper before calling it.
The [round-trip observer](../../../../../re/tooling/sw2026/ObserveEncoderRoundTrip.py) applies this rule to feature traversal and inspected values.
