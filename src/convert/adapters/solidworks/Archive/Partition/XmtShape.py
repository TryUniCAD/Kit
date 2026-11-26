from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField


# embedded schema changes must retain both the published base and effective field order
@DataClass(frozen=True, slots=True)
class XmtShape:
    NameValue: str
    BaseValue: tuple[XmtField, ...]
    FieldsValue: tuple[XmtField, ...]
