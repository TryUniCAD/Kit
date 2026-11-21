from pathlib import Path
import json
import sys


def main(request):
    here = Path(__file__).resolve()
    root = here.parents[5]
    sys.path[:0] = [str(here.parent), str(root / "src"), str(here.parents[2]),
                    str(here.parents[1] / "EndModes"), str(here.parents[1] / "PrincipalReader")]
    from ProveTwoDirectionRevolves import warm
    from ThinHeldoutPacket import require
    from ThinPublicRead import read_cold
    from ThinPublicWrite import rejection, write_candidate

    warm()
    if "negative" in request:
        answer = rejection(request)
    else:
        answer, original, fresh = write_candidate(request)
        answer["strict_readback"] = {"original": read_cold(original, request["case"], root / "src"),
                                     "fresh": read_cold(fresh, request["case"], root / "src")}
    require(not any(name == "Swapp" or name == "pythoncom" or name.startswith("win32com")
                    for name in sys.modules), "public SDK proof imported a native runtime")
    return answer


if __name__ == "__main__":
    try:
        result = {"passed": True, **main(json.load(sys.stdin))}
    except Exception as error:
        result = {"passed": False, "error_type": type(error).__name__}
        if "diagnostic" in sys.argv:
            result["diagnostic"] = repr(error)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    raise SystemExit(int(not result["passed"]))
