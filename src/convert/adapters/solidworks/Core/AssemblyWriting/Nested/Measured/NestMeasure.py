from dataclasses import dataclass as DataClass


# an authenticated assembly bundle fixes its exact full manifest and recorded view generation policy
@DataClass(frozen=True, slots=True)
class NestMeasure:
    WrittenAt: int
    ManifestSha: str
    ReportSha: str
    MemberCount: int
    PlatformMath: bool
