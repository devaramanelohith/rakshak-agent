"""Case / profile / alert storage. MemoryStore persists to data/runtime/*.json so a local demo survives a
restart; FirestoreStore (USE_FIRESTORE=true) is the Cloud Run path: durable across revisions and restarts."""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

from .config import settings

log = logging.getLogger("rakshak.store")

DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
    "demo-user": {
        "user_id": "demo-user",
        "name": "Lohith",
        "age_band": "25-39",
        "language": "en",
        "trusted_contact_name": "Priya (sister)",
        "trusted_contact_phone": "+91 98765 00007",
        "typical_transfer_inr": 4000,
        "guardian_enabled": True,
        "hold_threshold": settings.hold_threshold,
        "warn_threshold": settings.warn_threshold,
        "prior_alerts": 0,
    },
    "demo-user-hi": {
        "user_id": "demo-user-hi",
        "name": "Sunita Rao",
        "age_band": "60+",
        "language": "hi",
        "trusted_contact_name": "Priya (daughter)",
        "trusted_contact_phone": "+91 98765 00007",
        "typical_transfer_inr": 4000,
        "guardian_enabled": True,
        "hold_threshold": settings.hold_threshold,
        "warn_threshold": settings.warn_threshold,
        "prior_alerts": 0,
    },
    "demo-user-en": {
        "user_id": "demo-user-en",
        "name": "Daniel Tan",
        "age_band": "25-39",
        "language": "en-sg",
        "trusted_contact_name": "Mei (spouse)",
        "trusted_contact_phone": "+65 8000 0002",
        "typical_transfer_inr": 20000,
        "guardian_enabled": True,
        "hold_threshold": settings.hold_threshold,
        "warn_threshold": settings.warn_threshold,
        "prior_alerts": 0,
    },
}


class MemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.cases: dict[str, dict] = {}
        self.profiles: dict[str, dict] = {k: dict(v) for k, v in DEFAULT_PROFILES.items()}
        self.alerts: list[dict] = []
        self._load()

    # -- persistence ---------------------------------------------------------
    def _path(self, name: str):
        return settings.runtime_dir / f"{name}.json"

    def _load(self) -> None:
        for name in ("cases", "profiles", "alerts"):
            p = self._path(name)
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if name == "alerts":
                        self.alerts = data
                    else:
                        getattr(self, name).update(data)
                except Exception as e:  # pragma: no cover
                    log.warning("could not load %s: %s", p, e)

    def _save(self, name: str) -> None:
        try:
            data = self.alerts if name == "alerts" else getattr(self, name)
            self._path(name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:  # pragma: no cover
            log.warning("could not save %s: %s", name, e)

    # -- cases ---------------------------------------------------------------
    def put_case(self, case: dict) -> None:
        with self._lock:
            case["updated_at"] = time.time()
            self.cases[case["case_id"]] = case
            self._save("cases")

    def get_case(self, case_id: str) -> dict | None:
        return self.cases.get(case_id)

    def list_cases(self) -> list[dict]:
        return sorted(self.cases.values(), key=lambda c: c.get("created_at", 0), reverse=True)

    # -- profiles ------------------------------------------------------------
    def get_profile(self, user_id: str) -> dict:
        if user_id not in self.profiles:
            self.profiles[user_id] = {**DEFAULT_PROFILES["demo-user"], "user_id": user_id, "name": user_id}
        return self.profiles[user_id]

    def put_profile(self, user_id: str, patch: dict, user_edit: bool = False) -> dict:
        """``user_edit`` marks a change made by a person (PUT /api/profiles) rather than by the app."""
        with self._lock:
            prof = self.get_profile(user_id)
            prof.update({k: v for k, v in patch.items() if k != "user_id"})
            self._save("profiles")
            return prof

    # -- alerts --------------------------------------------------------------
    def add_alert(self, alert: dict) -> None:
        with self._lock:
            self.alerts.insert(0, alert)
            self.alerts = self.alerts[:200]
            self._save("alerts")

    def list_alerts(self, user_id: str | None = None) -> list[dict]:
        return [a for a in self.alerts if user_id is None or a.get("user_id") == user_id]


def to_firestore_doc(obj: Any) -> dict:
    """Snapshot a case/profile/alert into plain Firestore-safe types.

    A JSON round trip turns tuples into lists, int keys into strings and pydantic/other objects (via
    ``default``) into strings, and freezes the dict so later in-place mutation of the live case cannot race
    the background write. Firestore cannot hold an array directly inside an array, so any such inner list is
    stored as a JSON string."""

    def _default(o: Any) -> Any:
        if isinstance(o, (set, frozenset)):
            return sorted(o, key=str)
        if hasattr(o, "model_dump"):
            return o.model_dump()
        return str(o)

    def _fix(x: Any, in_list: bool = False) -> Any:
        if isinstance(x, list):
            if in_list:
                return json.dumps(x, ensure_ascii=False)
            return [_fix(v, True) for v in x]
        if isinstance(x, dict):
            return {(k or "_"): _fix(v) for k, v in x.items()}
        return x

    return _fix(json.loads(json.dumps(obj, ensure_ascii=False, default=_default)))


_FS_MAX_DOC_BYTES = 900_000  # Firestore limit is 1 MiB per document


class FirestoreStore(MemoryStore):  # pragma: no cover - needs GCP
    """Same interface, backed by Firestore (database ``(default)``).

    Collections (prefix from FIRESTORE_PREFIX, default ``rakshak``):
      * ``<prefix>_cases``    doc id = case_id   -> the full case (payment, rubric, payee, policy, decision, trace, timeline)
      * ``<prefix>_profiles`` doc id = user_id   -> the customer profile + ``_edited_fields`` (fields changed via PUT /api/profiles)
      * ``<prefix>_alerts``   doc id = alert_id  -> the trusted-contact alert

    The in-memory dicts stay the read path. Writes are snapshotted on the caller's thread and applied by a single
    background worker (ordered, off the request path), so a Firestore outage or slow write never delays the payment
    hold; failures are logged and the app carries on from memory. Firestore replaces the local JSON files."""

    def __init__(self) -> None:
        from concurrent.futures import ThreadPoolExecutor

        from google.cloud import firestore

        self.db = firestore.Client(project=settings.project)
        self.prefix = settings.firestore_collection_prefix
        self._edited: dict[str, set[str]] = {}
        self._writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="firestore-writer")
        super().__init__()  # defaults only: _load is a no-op below
        t0 = time.time()
        for doc in self._col("cases").stream(timeout=20):
            self.cases[doc.id] = doc.to_dict()
        for doc in self._col("profiles").stream(timeout=20):
            self._merge_loaded_profile(doc.id, doc.to_dict() or {})
        q = self._col("alerts").order_by("created_at", direction=firestore.Query.DESCENDING).limit(200)
        self.alerts = [d.to_dict() for d in q.stream(timeout=20)]
        log.info("Firestore loaded %d cases, %d profiles, %d alerts in %.1fs",
                 len(self.cases), len(self.profiles), len(self.alerts), time.time() - t0)
        # Seed / refresh the demo profiles so Firestore always shows what the app is actually using.
        for uid in DEFAULT_PROFILES:
            self._write_profile(uid)

    # -- helpers -------------------------------------------------------------
    def _col(self, name: str):
        return self.db.collection(f"{self.prefix}_{name}")

    def _merge_loaded_profile(self, user_id: str, data: dict) -> None:
        edited = set(data.pop("_edited_fields", None) or [])
        data.pop("_updated_at", None)
        self._edited[user_id] = edited
        default = DEFAULT_PROFILES.get(user_id)
        if default is None:
            self.profiles[user_id] = {**data, "user_id": user_id}
            return
        prof = self.profiles.setdefault(user_id, dict(default))
        for k, v in data.items():
            # A stale copy of a default field (name, language, contact...) must not override the code's defaults;
            # only fields a user changed through PUT /api/profiles, or extra state such as last_high_risk_call, load.
            if k == "user_id" or (k in default and k not in edited):
                continue
            prof[k] = v

    def _submit(self, what: str, fn, *args) -> None:
        def _run():
            try:
                fn(*args)
            except Exception as e:
                log.warning("Firestore write failed (%s): %s", what, str(e)[:200])
        try:
            self._writer.submit(_run)
        except Exception as e:  # executor shut down
            log.warning("Firestore write not queued (%s): %s", what, str(e)[:120])

    def _set(self, collection: str, doc_id: str, doc: dict) -> None:
        self._col(collection).document(doc_id).set(doc, timeout=15)

    def _write_profile(self, user_id: str) -> None:
        try:
            doc = to_firestore_doc(self.profiles[user_id])
            doc["_edited_fields"] = sorted(self._edited.get(user_id, set()))
            doc["_updated_at"] = time.time()
        except Exception as e:
            log.warning("profile %s not serialisable: %s", user_id, e)
            return
        self._submit(f"profile {user_id}", self._set, "profiles", user_id, doc)

    # -- persistence: Firestore replaces the JSON files ------------------------
    def _load(self) -> None:
        pass

    def _save(self, name: str) -> None:
        pass

    # -- writes ------------------------------------------------------------------
    def put_case(self, case: dict) -> None:
        super().put_case(case)
        try:
            doc = to_firestore_doc(case)
            if len(json.dumps(doc, ensure_ascii=False)) > _FS_MAX_DOC_BYTES:
                doc["trace"] = [{"note": "trace truncated to fit the Firestore document limit"}]
                doc["transcript_excerpt"] = str(doc.get("transcript_excerpt", ""))[:2500]
        except Exception as e:
            log.warning("case %s not serialisable: %s", case.get("case_id"), e)
            return
        self._submit(f"case {case['case_id']}", self._set, "cases", case["case_id"], doc)

    def put_profile(self, user_id: str, patch: dict, user_edit: bool = False) -> dict:
        prof = super().put_profile(user_id, patch, user_edit)
        if user_edit:
            self._edited.setdefault(user_id, set()).update(k for k in patch if k != "user_id")
        self._write_profile(user_id)
        return prof

    def add_alert(self, alert: dict) -> None:
        super().add_alert(alert)
        try:
            doc = to_firestore_doc(alert)
        except Exception as e:
            log.warning("alert not serialisable: %s", e)
            return
        alert_id = str(alert.get("alert_id") or f"alert_{int(time.time() * 1000)}")
        self._submit(f"alert {alert_id}", self._set, "alerts", alert_id, doc)

    def flush(self, timeout: float = 10.0) -> None:
        """Wait for queued writes (used by tests/shutdown)."""
        try:
            self._writer.submit(lambda: None).result(timeout=timeout)
        except Exception:
            pass


_store: MemoryStore | None = None


def store() -> MemoryStore:
    global _store
    if _store is None:
        if settings.use_firestore:
            try:
                _store = FirestoreStore()
                log.info("Using FirestoreStore")
            except Exception as e:
                log.warning("Firestore unavailable (%s); using MemoryStore", str(e)[:120])
                _store = MemoryStore()
        else:
            _store = MemoryStore()
    return _store
