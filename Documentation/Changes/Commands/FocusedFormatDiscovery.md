# Focused CLI format discovery

## Behavior

Task `B10-FormatDiscovery` adds `kit formats [FORMAT]` for case-insensitive identifier or alias lookup.
It reuses registry metadata rather than introducing another capability catalogue.
The unfiltered JSON contract remains a list.
A filtered success returns the same entry in a one-element list.
Unknown identifiers fail with a JSON error and recovery command on standard error.

Human output includes reader aliases and separate writer aliases when direction limits differ.
It ends with a registry-only reminder.
Use JSON output for machine processing.

## Usage and limits

Run `kit formats solidworks.sldasm --json` to inspect the assembly reader alias.
The entry still reports `.sldprt` as the only writer suffix and no assembly writer alias.
Lookup follows registry case folding and does not accept filename suffixes as identifiers.
Registration does not establish feature, version or cross-format acceptance.
No adapter, writer policy or conversion qualification changes.
See [the command-line procedure](../../Tasks/CommandLine.md).

## Verification

Source inspection at base `1619f00bf532caad262d1557bd69281179e5c497` identified the hidden text aliases and missing focused lookup.
The added process coverage in `tests/Convert/Commands/Discovery/CliFormatTests.py` exercises primary and alias queries, unknown identifiers, text limits and help.
It uses the existing CLI subprocess harness and shared suite discovery.
Focused steering passed for all six changed Python files.
Black formatting and Prettier checks passed for changed code and Markdown.
Process tests are deferred to remote CI under repository policy.
Native acceptance and representative-user evaluation were not performed.
