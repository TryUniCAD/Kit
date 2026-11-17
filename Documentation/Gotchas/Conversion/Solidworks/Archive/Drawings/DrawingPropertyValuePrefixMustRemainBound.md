# Drawing property-value prefix must remain bound

A namespace-correct generated document can open successfully and still be incompatible with the vendor's later DOM edits. The previous drawing property XML used an automatically selected `ns1` prefix for the property-value namespace. It did not declare `vt`.

The native loader retains the supplied SolidWorks-information DOM. Its writer appends literal `vt` element names through MSXML `createElement`, which does not assign a namespace URI. It then reparses the resulting XML. The constructor vocabulary explicitly declares `vt`; an alternative binding for the same URI does not provide that literal prefix. [Pinned source and exact prior failure](../../../../../../re/solidworks/records/DrawingPropertyPrefix2026.md)

Generate the `vt` declaration on the property document itself and use the matching literal prefix for typed children. Keep unqualified property-section and dictionary records unqualified. Do not change ElementTree's process-wide namespace registry to repair one document. Continue to require native edit, save and fresh reopen; the prefix-only candidate's native result is pending.
