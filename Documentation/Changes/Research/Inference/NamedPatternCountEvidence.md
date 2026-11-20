# Competing encodings in named scalar records

The SOLIDWORKS generated reader checks a named scalar offset against the bounded pattern feature that owns the record. If the feature's integer declaration matches bytes at that offset, the ownership report retains all matching integer encodings and searches the remaining feature window for literal floating-point copies of the declared count. It tags the field as a pattern count hypothesis and retains the raw floating-point interpretation for inspection.

Run the single-input research CLI and inspect count_hypothesis in the resolved member's ownership records. Each copy has its own absolute member offset and encoding. Coincidental numeric matches remain possible. These same-file observations do not train a transferable rule, prove integer width or establish the count through a native application.
