# SOLIDWORKS model exchange maps can repeat keys

The ordinary SOLIDWORKS 2026 model exchange stores ordered MessagePack pairs. A mate group record contains `class` twice with different values, and the configuration table of contents repeats `object` for its different groups. Converting these maps to Python dictionaries drops actual owners.

Retain the ordered pairs. Require uniqueness only for the fields whose specific owner defines a single value, such as `TOC.model.configid` and `TOC.model.configname`. [Verified examples](../../../../../../re/solidworks/records/ConfigHeaderExchange2026.md)
