# Original assembly save contrast for the planar renderer

The supplemental research observer compares a native save of a copied
original assembly and its driven child with the prior generated pair.
It applies the same live depth edit in the actual bound child, checks the
preserved original hashes, reopens the saved copy in a fresh process and
reports child renderer owners and the Definition allocator cursor.

Use the pinned completed planar renderer packet and a fresh sibling output
directory. The script's SHA-256 goes in `--tool-pin`. The host preflight
verified the exact packet and decoded the allocator and renderer roles in
both original children. The first native attempt stopped before edits
when both parent copies located their original children. With
`--rebind`, the probe explicitly binds each closed parent copy to its
verified child copy before live edits.
[Method and custody](../../../../../re/solidworks/records/PlanarRendererNativeMethod2026.md)
