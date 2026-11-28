# Style wire occurrences differ from runtime fields

A complete computed constructor and a raw decoded style have different key sets. Comparing their dictionaries directly can reject matching serialized state.

The ordinary `moSwiftGtsOptions_c` serializer writes runtime `f220` three times. The raw codec retains the separate occurrences as `f220#0`, `f220#1` and `f220`. The constructor has one `f220` member and also initializes `f250`, `f260` and `f3dc`, which are absent from the current 159-scalar wire layout. The private origin normalizer initially compared these different representations and refused four generated children at `model.fae0.ff68`.

Project the independently computed expected constructor through the exact current field vocabulary. Use each declared `OtherName` only for its named wire occurrence. Compare every actual source field, including all three repeated words, against that computed wire view. Report constructor-only fields separately. Do not collapse the raw source words, ignore arbitrary extra keys, or use the source values to fill the expected constructor.

The [native common-owner record](../../../../../../re/solidworks/records/CommonPartOwners2026.md) binds all 159 occurrences and the three actual store calls. The [style construction record](../../../../../../re/solidworks/records/StyleConstruction2026.md) classifies the fresh runtime state. The observer correction changes neither codec nor constructor output.
