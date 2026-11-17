# Sorted JSON keys change authored part-folder order

## Expectation

A neutral part recipe can survive canonical JSON encoding without changing its ordered native feature tree.

## Actual behavior

The research model constructor deliberately consumes `folder_names` in mapping insertion order. The original child recipe authored comments, favorites, history and other folders in a particular sequence. A later helper encoded that mapping with `sort_keys=True`, so the receiving process constructed the same folders in alphabetical class order.

The disclosed drawing rehearsal passed all eight native phases and both controls, but exact paired comparison failed on the child system-tree order in all five states. Its 27-row node multiset was unchanged. Treating the tree as an unordered set would hide the lost authored sequence.

## Workaround

Carry a meaningful sequence as a JSON array. The research constructor now accepts `presentation.folder_order`, validated as an exact permutation of the existing folder class keys. Obtain it from independent authored input or a qualified source model, never from a per-case captured output table. Omitting it retains the old mapping behavior for compatibility.

The native storage walk preserves linked-list traversal order. There is no general native alphabetical-folder requirement. The corrected disclosed candidate still requires native comparison before the original held-outs may be unsealed.

See [the field and process evidence](../../../../../../re/solidworks/records/PartFolderOrder2026.md) and [the change entry](../../../../../Changes/Solidworks/Model/Ordering/SolidworksAuthoredPartFolderOrder.md).
