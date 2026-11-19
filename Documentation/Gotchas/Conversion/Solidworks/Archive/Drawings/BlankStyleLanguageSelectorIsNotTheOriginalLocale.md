# A fresh blank style selector is not its original locale

The fresh style constructor accepts a `LanguageId`, but its ten annotation styles encode only `2 if LanguageId & 1023 == 13 else 0`. The actual History locale is a separate stored owner. Reading History and treating it as the exact original style input can change source rendering state.

Independent generated Mu and Nu controls use differing style/history locale inputs. Complete file reconstruction preserves the actual History locale and the encoded annotation selector effect. The full original style locale cannot be recovered from that effect alone. This fact is scoped to the existing fresh `MakeDetails`/`MakeAnnoStyle` construction profile; it is not a claim about every native SOLIDWORKS style.

Recover all ten actual selector fields, require a consistent supported effect, and choose a legal reconstruction representative. Keep the real History locale unchanged and mark the style selector as representative in retained metadata. Do not describe that representative as a recovered original authoring locale. [Owner record and exact process evidence](../../../../../../re/solidworks/records/SdkGeneratedBlankStrictReader2026.md)
