# Sketch count review coverage

The research CLI integration case now checks decoded sketch pattern counts in `Input-strict.json`.
Each count must have an integer value, an empty unit, and no inferred native measurement.
The decoded sketches must retain these parameters without distance constraints for their counts.

Count pairing, count projection, and radial operand matching now have focused implementation modules.
Research scripts import count-field discovery from its defining module.
The affected integration cases use repository naming rules and focused receipt checks.

Verification: source inspection, Black 26.10.1, Ruff, and the repository steering checker.
No local tests ran.
The integration cases await remote acceptance execution.
These changes do not establish lossless conversion or vendor acceptance.

The [Black exclusion gotcha](../../../Gotchas/Tooling/BlackCoreExclusion.md) explains why Core paths were checked through standard input.
