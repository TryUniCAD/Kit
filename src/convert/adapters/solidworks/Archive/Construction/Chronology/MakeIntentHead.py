from convert.adapters.solidworks.Archive.Construction.Chronology.CheckLogOwners import (
    CheckLogOwners,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.HeaderClocks import (
    HeaderClocks,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeRevBook import (
    MakeRevBook,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import (
    RevisionBook,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakePartHeader import (
    MakePartHeader,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# source intent needs a separate header factory while existing fresh output policies remain byte exact
def MakeIntentHead(
    ModelValue: ArchiveNode,
    ClocksValue: HeaderClocks,
    BookValue: RevisionBook,
    Allocator: PersistentIds,
    ModelPresent: bool,
) -> ArchiveNode:
    if type(ClocksValue) is not HeaderClocks or type(BookValue) is not RevisionBook:
        raise ValueError(
            "header construction requires explicit typed source intentions"
        )
    CheckLogOwners(ModelValue, BookValue)
    SeedValue = HeaderInput(
        BookValue.UsersValue[0],
        BookValue.CompaniesValue[0],
        "",
        ClocksValue.CreatedAt,
        max(ClocksValue.CreatedAt, ClocksValue.ArchiveAt),
        ClocksValue.UpdatedAt,
    )
    HeaderValue = MakePartHeader(ModelValue, SeedValue, Allocator, ModelPresent)
    GraphValue = MakeRevBook(BookValue)
    HeaderValue.FieldsValue.update(
        {
            "f10": GraphValue.UsersValue,
            "f18": GraphValue.CompaniesValue,
            "f20": GraphValue.LogsValue,
            "f50": ClocksValue.ArchiveAt,
        }
    )
    return HeaderValue
