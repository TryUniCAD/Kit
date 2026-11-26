# Manager header roles constrain traversal

The lightweight configuration directory contains two concrete class
descriptors. A shared class allowlist alone permits a second manager
to open inside the embedded configuration list. This would add a
second list and recurse through the node and field callbacks.

Check the expected class and schema before a new body reads its
fields. The manager occupies depth one and configuration leaves
occupy depth two. Check list entries after traversal too. Null and
reference tags return without opening another body, so those entries
still need to match the configuration header role.
[Native directory construction](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigurationManagerHeader2026.md)
[Role refusal process](../../../../../../tests/Convert/Solidworks/CmgrHeader/ManagerRoleTests.py)
