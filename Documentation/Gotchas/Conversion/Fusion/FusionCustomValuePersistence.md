# Registered members do not always determine custom value wire order

Most captured entity groups persist eligible members in lexical name order, but a custom value callback can supply its own order.
Applying the generic lexical rule to `ColorValueMetaType` produced byte-exact reconstruction while assigning the wrong color component names to the four stored floats.

`ColorDataModelCallback::onSave` in the recorded `nsTypes10` image explicitly calls red, green, blue and alpha accessors and writes four binary32 values in that order.
The arm64 entry is `0x4d6c0`, with writes at `0x4d714`, `0x4d734`, `0x4d754` and `0x4d774`.
The corrected reader/writer uses RGBA order, and comparison with native property observations now matches those names and values.

The [callback audit](../../../../re/Fusion/Reconstruction/EntityGraph/ValueCallbacks.json) and [typed graph summary](../../../../re/Fusion/Reconstruction/EntityGraph/GraphSummary.json) preserve the evidence.
Byte-identical re-encoding alone proves framing, not correct field semantics. Audit custom save callbacks and compare named values with native observations before promoting their schema.
