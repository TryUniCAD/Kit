from typing import cast

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# paginated inventories cannot silently omit changed files or previous reviews
def ReadPages(Route: str) -> list[dict[str, object]]:
    Records: list[dict[str, object]] = []
    for PageNum in range(1, 32):
        PageData = ApiCall(f"{Route}?per_page=100&page={PageNum}")
        if not isinstance(PageData, list):
            raise ValueError("Expected an API list")
        Entries = cast(list[object], PageData)
        Records.extend(ObjectMap(Entry) for Entry in Entries)
        if len(Entries) < 100:
            return Records
    raise ValueError("API inventory exceeded review limit")
