# Sorted refusal reports and historical digests

Replacing a JSON key in place does not restore the original sorted report order.
`VerifySignedPrism.py` sorts keys before serialization.
The newer `reverse_formula` key sorts before `reverse_inch_display`.
The historical `unwrapped_literal` key belongs immediately before `wrapped_taper`.
An in-place key replacement therefore still fails the pinned digest.

Remove the exact new refusal line and insert the exact historical line at its sorted position for comparison only.
Require unique matches, exact indentation and commas, and the expected order.
Preserve every other byte and the original digest.
The actual verifier report must retain the real case name and diagnostic.
See [the review finding](https://github.com/TryUniCAD/Kit/pull/285#discussion_r4681150943).
