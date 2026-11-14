"""Pre-registration guard.

Until the OSF registration exists, BRFSS/MEPS outcome data (BMI, obesity, height) must not be analysed
(pre-registration Q18). Every loader of real outcome data calls `require_registration()`, which refuses to run
until docs/osf_registration.txt holds the registration DOI or URL. The analysis functions themselves are pure
and are tested on simulated data only.
"""

from pathlib import Path

from glp1_review.paths import DOCS

REGISTRATION_FILE: Path = DOCS / "osf_registration.txt"


class NotRegisteredError(RuntimeError):
    pass


def registration_id() -> str | None:
    if not REGISTRATION_FILE.exists():
        return None
    text = REGISTRATION_FILE.read_text(encoding="utf-8").strip()
    return text or None


def require_registration() -> str:
    reg = registration_id()
    if reg is None:
        raise NotRegisteredError(
            "Outcome data cannot be analysed before the OSF registration (pre-registration Q18). "
            f"After registering, write the registration DOI/URL to {REGISTRATION_FILE}."
        )
    return reg
