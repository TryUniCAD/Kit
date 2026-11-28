# SOLIDWORKS assembly source controls

The 2026 research corpus now includes `A0_one.SLDASM` and `A1_two.SLDASM`,
containing one and two component instances respectively. The accompanying
manifest records original and privacy-redacted hashes, exact native build,
save results, component names, raw mate API results and observed dialog/error
counts. They are training inputs for source-grammar recovery, not generated
writer output or held-out acceptance.

`PrepareCorpus.py --kind assembly` prepares this corpus from the oracle's
`manifest.json` and `.SLDASM` files. Its default part mode remains available.
Metadata redaction preserves encoded width; the container is rebuilt from the
same source. The tool deliberately reads native source files to create research
fixtures and is not called by a production writer.

The original native saves returned success with error/warning values zero.
Assembly source diagnostics recorded `GetWhatsWrongCount=0`. Mate calls retain
their raw result code 1 without assigning an unrecovered enum meaning. The
research assembly byte-identity check will run remotely as its shared grammar
is extended. No local tests were run, and these fixtures do not establish
native generated-file acceptance.
