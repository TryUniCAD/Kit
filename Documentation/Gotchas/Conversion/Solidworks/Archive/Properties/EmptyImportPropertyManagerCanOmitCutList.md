# Empty import property managers can omit the cut list

An ordinary property manager can have a keyed container with an empty
concrete file-property owner and a null cut-list pointer. All four
disclosed SOLIDWORKS 2026 SP05.2 local import parts carry that state.
Insisting on a separate empty cut-list object withheld the ordinary text
projection even though their three XML property scopes were empty.

Consume the complete manager graph. Treat a null
`moCusPropContainer_c.f10` as absence of a cut-list scope. When present,
verify the schema-one class and both of its row collections. The concrete
file owner, empty lists, manager policy, null third owner and XML scope
checks still apply.
[Field record](../../../../../../re/solidworks/records/PartEmptyAdvancedProperties2026.md)
[Measured controls](../../../../../../re/solidworks/measurements/2026/ImportedLocalPartSemantics01.json)
