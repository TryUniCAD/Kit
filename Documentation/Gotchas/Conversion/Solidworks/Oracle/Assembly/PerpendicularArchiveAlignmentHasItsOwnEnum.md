# Perpendicular archive alignment and COM alignment have different enum domains

An API alignment value must not be copied into the archive's internal alignment field. In the disclosed 2026 D01 perpendicular source and its independently saved edited sibling, `IMate2.Alignment` returns `2` while `moMate.f3b4` is `0`. The separate solved-state field `f3b8` is `1` in both files.

The pinned perpendicular command independently explains the zero: the API enum2 branch passes zero into the ordinary command constructor instead of the translated explicit alignment used by coincident and parallel mates. The observed COM result is a different API enumeration. It does not establish internal anti-alignment or an explicitly aligned relationship.

Keep the neutral alignment `unknown` for this measured perpendicular branch, retain the raw internal alignment and solved-state codes, and verify actual ordered occurrence/child-datum identities and orthogonal plane normals. Preserve the observed COM code only in native measurement evidence. Other internal or API values need their own binding before admission.

[Command path](PerpendicularMateIgnoresAlignment.md) · [Exact field and source reconciliation](../../../../../../re/solidworks/records/PerpendicularMateReadOwnership2026.md) · [Sanitized read receipt](../../../../../../re/solidworks/measurements/2026/PerpendicularMateDisclosedRead01.json)
