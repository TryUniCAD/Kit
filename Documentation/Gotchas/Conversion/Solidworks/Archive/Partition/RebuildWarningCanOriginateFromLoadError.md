# Rebuild warning can originate from a load error

**Expectation:** public warning 32 must be published by the native load-warning method with argument 32.

**Actual behavior:** exact SOLIDWORKS 2026 `auAm::apiOpenDoc` translates internal `appApiFileLoadError` value 128 into warning bit 32 for its API argument at least 5. This is an API compatibility gate, not the document archive version. The disclosed part diagnostic captured that internal error from the actual `uiPartDoc::iiConfigureMAIN` override. A separate `askToRegen` path can publish the same internal code.

**Workaround:** preserve the actual record class, incoming value, caller and API argument before interpreting the returned warning. Source-bound observation of the producer avoids missing the error-to-warning route. A zero configuration rebuild query, an accepted kernel body or a void publication return does not erase the warning. [Exact build, spans, original switch tables and diagnostic limits](../../../../../../re/solidworks/records/PartRebuildWarning2026.md)
