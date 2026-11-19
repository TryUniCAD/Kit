from __future__ import annotations


# this definition exists because focused behavior needs one stable owner
class FreeCadAdapterA(RuntimeError):

    # this definition exists because focused behavior needs one stable owner
    def __init__(self, Message: str) -> None:
        super().__init__(Message)
