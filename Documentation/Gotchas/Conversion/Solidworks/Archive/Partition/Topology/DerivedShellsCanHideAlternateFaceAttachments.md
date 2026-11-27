# Derived shells can hide alternate face attachments

In the witnessed attributed active partition, the body-owned solid shell
starts its boundary at `face`. The separate void shell starts its boundary
at `front_face`. The complementary pointer on each shell is zero.

Setting either complementary pointer to a real face leaves the primary
chains and reference classes valid. The derived shell used by the neutral
builder can still look identical because that builder never consumes the
alternate pointers. When reading this bounded profile, resolve the native
shell roles and reject a populated complementary pointer before projection.

[Maintained attributed partition checks](../../../../../../../re/tooling/sw2026/attributed_read/CheckAttributedFaults.py)
