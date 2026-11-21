from contextlib import contextmanager
import json
import os

from PatternParityPacket import checked, digest, encode, exclusive, require


@contextmanager
def private_lock(home):
    from msvcrt import LK_NBLCK, LK_UNLCK, locking

    with (home / "Transport.lock").open("a+b") as stream:
        if not stream.tell():
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        locking(stream.fileno(), LK_NBLCK, 1)
        try:
            yield
        finally:
            stream.seek(0)
            locking(stream.fileno(), LK_UNLCK, 1)


def paths(home):
    return (home / "Locator.json", home / "PriorOriginal.SLDPRT",
            home / "ExactCandidate.SLDPRT", home / "ObservedWorking.SLDPRT")


def lease_row(locator, prior, candidate, pin):
    return {"schema": "kit.sw2026.same-pattern-locator.v1", "packet_sha256": pin, "locator": str(locator),
            "prior_sha256": prior, "candidate_sha256": digest(candidate)}


def install(home, locator, prior, candidate, pin):
    journal, parked, staged, observed = paths(home)
    require(all(not path.exists() for path in (journal, parked, staged, observed)), "locator lease already has evidence")
    checked(locator, prior)
    exclusive(staged, candidate)
    row = lease_row(locator, prior, candidate, pin)
    with journal.open("xb") as stream:
        stream.write(encode(row))
        stream.flush()
        os.fsync(stream.fileno())
    os.rename(locator, parked)
    checked(parked, prior)
    os.rename(staged, locator)
    checked(locator, row["candidate_sha256"])


def restore(home, locator, prior, candidate, pin):
    journal, parked, _, observed = paths(home)
    if not journal.exists():
        checked(locator, prior)
        return
    require(not journal.is_symlink() and not journal.is_junction()
            and json.loads(journal.read_bytes()) == lease_row(locator, prior, candidate, pin),
            "locator recovery journal changed")
    if parked.exists():
        checked(parked, prior)
        if locator.exists():
            require(not locator.is_symlink() and not locator.is_junction() and locator.is_file(),
                    "unexpected object at the original candidate locator")
            if digest(locator.read_bytes()) == prior:
                return
            require(not observed.exists(), "private observed candidate destination already exists")
            os.rename(locator, observed)
        os.rename(parked, locator)
    checked(locator, prior)
