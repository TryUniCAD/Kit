# Plane wrappers can omit inline geometry

## Expectation

A component-plane wrapper always contains the referenced plane node.

## Observed behavior

The 2026 wrapper constructor retains inline geometry only for a plane whose
persistent id is `-1`.
An allocated plane is represented through its component and feature-reference
data; its inline geometry pointer stays null.
The principal-plane kind also follows the semantic plane type and normal.
A display name alone does not establish that kind.
The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
lists the constructor and discriminator evidence.

## Workaround

Build the owning model and allocate plane ids before constructing wrappers.
Resolve the symbolic owner and feature references through the archive map.
Derive the principal kind from semantic plane data.
Do not force every wrapper to contain another copy of the plane.
