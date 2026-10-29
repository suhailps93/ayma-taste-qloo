"""Make the extracted Qloo backend importable in isolation.

Adds the backend dir (the real hackathon-new modules: ``qloo_client``,
``taste_match``, ``config``) and the ``_stubs`` dir (clearly-labelled stand-ins
for Ayma's private core — auth, db, feature_flags, public_profile, story, the
age-gate dependency; see ``_stubs/README.md``) to ``sys.path``. The backend dir
is inserted FIRST so a real deliverable module always wins over anything in
``_stubs``; the stubs only resolve the private-core imports that have no public
module here.

Tests run isolated from any real credentials, so ``QLOO_API_KEY`` is cleared for
the whole session (no test makes a live Qloo call — the bundled fixture stands
in for Qloo).
"""

import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_STUBS = _BACKEND / "_stubs"

for p in (str(_STUBS), str(_BACKEND)):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
# Backend must take precedence over _stubs for shared names.
sys.path.remove(str(_BACKEND))
sys.path.insert(0, str(_BACKEND))

os.environ.pop("QLOO_API_KEY", None)
