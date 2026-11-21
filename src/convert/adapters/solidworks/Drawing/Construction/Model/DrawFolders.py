from dataclasses import dataclass as DataClass


# drawing folder identities must come from explicit authored names rather than installed templates or resource lookups
@DataClass(frozen=True, slots=True)
class DrawFolders:
    CabinetName: str
    BinderName: str
    CommentsName: str
    BlocksName: str
    InkName: str
    ReviewName: str
