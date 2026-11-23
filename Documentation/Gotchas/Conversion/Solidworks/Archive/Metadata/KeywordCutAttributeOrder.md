# Native cut keyword attributes have a separate order

The keyword index tests complete wire bytes, including XML attribute
order. Eight independently disclosed native cut rows put
`DissectableChildren` before `DissectableRoot`. The existing generated
profile emits the two attributes in reverse order.

Use the classified native row grammar when reconstructing the saved
index. Retain the published generated profile when regenerating its
measured output. [Typed corpus evidence](../../../../../../re/solidworks/records/KeywordTypedCorpus2026.md)
