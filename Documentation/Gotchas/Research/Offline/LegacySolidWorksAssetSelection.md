# Legacy SOLIDWORKS asset selection

## Expectation

Repeating `--asset` can appear to select several SOLIDWORKS parts.

## Actual behavior

Legacy trusted checkouts use a single-value parser option and select the last supplied asset.
The singleton command retains this behavior for compatibility.

## Workaround

Use the explicit `--batch` flag when you supply several parts.
Older research checkouts reject the flag before writing artifacts.
Select a checkout with batch support, or run one singleton command per part.
See [the research CLI procedure](../../../Tasks/ResearchCommandLine.md#decode-committed-inputs).
