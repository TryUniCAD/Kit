# Repeated sketch creation keeps existing profile features

Creating the second stock sketch in a native revolve-cut part leaves
the first stock's consumed `ProfileFeature` in the top-level enumeration.
The single-sketch author's scan therefore stopped on the second stock
before the cut existed. Both known-good controls passed.

Record the actual existing profile names before inserting a sketch.
Verify that exactly one profile was added, obtain its sketch interface,
then verify the selected construction line against the actual profile.
[Cut discovery failure receipt](../../../../../../re/solidworks/measurements/2026/RevolveCutDiscoveryFailed01.json)
