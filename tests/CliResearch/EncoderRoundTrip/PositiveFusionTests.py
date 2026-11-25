from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.EncoderRoundTrip.FreshCuboid import FreshCuboid
from tests.CliResearch.EncoderRoundTrip.PreserveRetry import PreserveRetry
from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder
from tests.CliResearch.EncoderRoundTrip.VerifyCandidate import VerifyCandidate


# fresh authored native inputs must exercise candidate generation and preserve explicit driving geometry through the installed command
@TestMark.parametrize("EditedHeight", (14.2, 5.3))
def CheckFusionFlow(TmpPath: FilePath, EditedHeight: float) -> None:
    WidthMm, DepthMm, HeightMm = 23.4, 17.8, 5.3
    SourcePath, OutputPath = TmpPath / "Source.f3d", TmpPath / "RoundTrip"
    SourceBytes = FreshCuboid(SourcePath, (WidthMm, DepthMm, HeightMm))
    Result = RunEncoder(
        TmpPath,
        "fusion",
        SourcePath,
        OutputPath,
        str(EditedHeight),
        LocatorValue=r"C:\KitEncoderRoundTrip",
    )
    IsNoop = EditedHeight == HeightMm
    assert Result.returncode == (3 if IsNoop else 0), Result.stderr
    Manifest = DecodeJson((OutputPath / "manifest.json").read_bytes())
    assert Manifest["status"] == ("incomplete" if IsNoop else "awaiting_native")
    assert Manifest["source"]["status"] == "decoded"
    assert Manifest["source_sha256"] == HashContent(SourceBytes).hexdigest()
    assert Manifest["models_used"] is False
    assert Manifest["vendor_loadable"] is False
    assert Manifest["application_usable"] is False
    Cases: tuple[tuple[str, float], ...] = (("reconstruction", HeightMm),)
    if IsNoop:
        assert Manifest["edited"]["status"] == "unsupported"
        assert "must change the driving value" in Manifest["edited"]["reason"]
        assert not (OutputPath / "edited.f3d").exists()
    else:
        Cases += (("edited", EditedHeight),)
    for RoleName, ExpectedHeight in Cases:
        assert Manifest[RoleName]["status"] == "awaiting_native"
        VerifyCandidate(
            OutputPath / (RoleName + ".f3d"),
            (WidthMm, DepthMm, ExpectedHeight),
            Manifest["candidate_sha256"][RoleName],
        )
    assert SourcePath.read_bytes() == SourceBytes
    if IsNoop:
        PreserveRetry(TmpPath, SourcePath, OutputPath, EditedHeight)
