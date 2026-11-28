import subprocess as ProcessTools
from tempfile import TemporaryFile


# hosted failures need actionable categories without exposing account credentials or untrusted model output
def RunProcess(Arguments: list[str], Prompt: str) -> None:
    with TemporaryFile() as ErrorFile:
        Result = ProcessTools.run(
            Arguments,
            input=Prompt,
            text=True,
            check=False,
            timeout=1800,
            stdout=ProcessTools.DEVNULL,
            stderr=ErrorFile,
        )
        if Result.returncode == 0:
            return
        ErrorFile.seek(max(0, ErrorFile.tell() - 65536))
        ErrorText = ErrorFile.read().decode(errors="replace").lower()
    for Marker, Category in (
        ("refresh_token_reused", "account refresh token was already rotated"),
        ("refresh token", "account refresh failed"),
        ("401 unauthorized", "account authentication was rejected"),
        ("model_not_found", "requested model is unavailable"),
        ("not supported", "requested capability is unsupported"),
        ("unknown feature", "runtime feature configuration was rejected"),
        ("unexpected argument", "runtime command configuration was rejected"),
        ("permission denied", "runtime filesystem or sandbox permission was denied"),
        ("bwrap:", "linux sandbox initialization failed"),
        ("landlock", "linux sandbox initialization failed"),
        ("operation not permitted", "container operation was denied"),
        ("error sending request", "account service connection failed"),
        ("rate limit", "account service rate limit was reached"),
        ("quota", "account service quota was reached"),
    ):
        if Marker in ErrorText:
            raise RuntimeError(f"Review runtime failed: {Category}") from None
    raise RuntimeError(f"Review runtime exited with status {Result.returncode}")
