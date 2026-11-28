# Downstream enable does not select body options

**Expectation:** enabling downstream IDs or reading the adjacent diagnostic initialization establishes the optional body `f90` flag.

**Actual behavior:** the exact 2026 model image has independent DWORDs. Application/diagnostic enable state reaches the ordinary downstream gate, while `f90` additionally tests bit `0x10` in a separate options word. That word is initially zero by the PE zero-fill rule. Its exported setter replaces the whole DWORD. The three adjacent dump-option callbacks stop before the word; the next container initializer starts after it.

**Workaround:** keep the enable state, fresh loader options and actual runtime options separate. Do not OR `0x10`, copy a saved body list or infer a runtime default from a zero named-import search. Bind an actual runtime value or its complete source producer before claiming that the ordinary application selects body rows.

The [source record](../../../../../../../re/solidworks/records/DownstreamBodyOptions2026.md) includes original hashes, source ranges, negative-search scope and the minimal read-only observation that can close the current runtime gap. No option or application preference was changed.
