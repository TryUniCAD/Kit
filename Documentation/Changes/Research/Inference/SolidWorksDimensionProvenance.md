# SOLIDWORKS dimension provenance

Run `kit decode PART --from solidworks.sldprt -o document.json` to inspect the strict reader. Feature and sketch pattern counts use an integer with an empty unit. A declared count can be known while its binary location remains unresolved. Sketch count parameters do not create distance constraints. An unbound angle retains its displayed degrees and has no native value or unit.

A matching display and driving pair can refine a rounded metric sketch length even when the driving span was already bound. The reader checks both records’ operands, measurement and display precision before using the saved scalar. A radius or diameter can point to construction geometry without forming a closed profile.

A local CLI decode of `RUEDA DE TURBINA.SLDPRT` produced counts of 11 for features 65 and 257, 32.73 degrees for feature 65 D2, and 39.41420312445611 mm for feature 66 D2 from offset 49223. These observations cover reader output. They do not establish editable conversion or vendor acceptance.

The held-out P04 cut-width edit independently reproduced the 6 mm bottom offset. The research CLI also requires an identity check for every selected Fusion manifest before publishing its text reader. Each control records the hash of its manifest member.
