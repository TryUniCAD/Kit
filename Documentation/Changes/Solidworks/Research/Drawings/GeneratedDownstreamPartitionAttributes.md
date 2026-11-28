# Generated downstream partition attributes

The SOLIDWORKS research writer generates face and edge IDs on an ordinary solid part's linked topology. It uses the native shared counter and carries the model's UUID-derived key and update time in each integer attribute. The same implementation serves rectangular and cylindrical bosses.

Add `src`, the repository root, `re/tooling/sw2026` and `re/tooling/sw2026/serial` to `PYTHONPATH`. Run `python -B -m drawing_edges.CheckDownstreamPartition prism 1`. The `prism` and `cylinder` profiles each have two cases.

Eight fresh processes reproduce all attributed partitions and verify each word against an independent calculation with zero runtime inputs. The related compatibility replay preserves prior partition results. Public writing, the complete drawing cache and SOLIDWORKS acceptance remain pending. [Rules and replay](../../../../../re/solidworks/records/GeneratedDownstreamPartition2026.md)
