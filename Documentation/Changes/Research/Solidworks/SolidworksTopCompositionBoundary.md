# Audit full Top annotation construction from JSON

The research command verifies a complete generated `.SLDPRT` from one named owned-neutral JSON request in a fresh Python process.
It guards construction against external inputs and checks the full archive through the public strict SDK reader.
It also checks input preservation and explicit refusals for unsupported annotation intent, metadata, provenance and retained native bytes.

See the [procedure and evidence](../../../../re/solidworks/WriterResearch/TopCompositionBoundary.md) for usage and exact revision identities.

Two Python 3.14.6 executions returned zero with byte-identical reports.
The generated 9,390-byte archive matched the candidate owner's exact digest.
Strict SDK readback reported one solid and linked configuration/resolved maps.
All 18 unsupported requests refused without changing the input.
Construction made no external reads.
Readback made one declared packaged-grammar read, recorded separately from the named model-input read.

The [grammar-read gotcha](../../../Gotchas/Research/Readers/SolidWorksVendor/PackagedGrammarReadIsNotSourceAccess.md) explains that distinction.
This evidence does not establish native acceptance, source-native provenance preservation, held-out proof or production support.
Both native acceptance flags remain false.
