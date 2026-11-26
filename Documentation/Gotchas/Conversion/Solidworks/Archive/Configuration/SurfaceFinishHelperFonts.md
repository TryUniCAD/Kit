# A finish helper stores two font bodies

An ordinary surface-finish helper stores a font at `fc0`. Its inline
annotation helper at `f128` then stores another font at `f08`.
Both fonts match in each of the two disclosed parts, although their
serialized lengths differ between the parts. The three finish roles in each
part consume both font bodies and allocate no archive slots.

Keep the finish font and the annotation font in their own fields.
Reuse the character-format grammar for each. The guarded authored
case uses different formats and names and checks the entire record.
[Physical spans and authored contrast](../../../../../../re/solidworks/records/ConfigSurfaceFinish2026.md)
