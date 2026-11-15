# PE symbol budgets can hide valid entries

## Expectation

The PE parser returns every import and export from a valid vendor DLL.

## Observed behavior

The installed parser limits both import symbols and export symbols to 8,192
by default. The studied 2026 model DLL has 45,857 export entries.
The default scan exposed only part of its symbols and import descriptors.
A missing annotation therefore did not establish a missing binary API.

## Workaround

The research disassembler uses explicit budgets of 100,000 import and export
symbols and prints parser warnings.
Keep the budget and any remaining truncation visible in analysis evidence.
Do not infer absence from a limited inventory.
