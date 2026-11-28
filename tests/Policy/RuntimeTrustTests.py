from pathlib import Path
from ssl import create_default_context
from subprocess import run
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import urlopen


# exported public authorities must establish verified tls before the account runtime can contact its service
def CheckRuntimeTls() -> None:
    with TemporaryDirectory() as TempName:
        TrustPath = Path(TempName) / "Certificates.pem"
        run(
            [
                "node",
                str(
                    Path(__file__).resolve().parents[2]
                    / ".github/scripts/Review/Runtime/WriteTrust.cjs"
                ),
                str(TrustPath),
            ],
            check=True,
            capture_output=True,
            timeout=20,
        )
        TrustData = create_default_context(cafile=str(TrustPath))
        assert TrustData.cert_store_stats()["x509_ca"] > 0
        try:
            with urlopen(
                "https://chatgpt.com/", context=TrustData, timeout=30
            ) as Response:
                StatusCode = Response.status
        except HTTPError as ErrorInfo:
            StatusCode = ErrorInfo.code
            ErrorInfo.close()
        assert 100 <= StatusCode < 600
