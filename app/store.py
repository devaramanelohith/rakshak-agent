"""Case / profile / alert storage. MemoryStore persists to data/runtime/*.json so a demo survives a
restart; FirestoreStore is the Cloud Run path (multi-instance safe)."""
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

    def put_profile(self, user_id: str, patch: dict) -> dict:
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


class FirestoreStore(MemoryStore):  # pragma: no cover - needs GCP
    """Same interface, backed by Firestore (keeps an in-memory read cache)."""

    def __init__(self) -> None:
        from google.cloud import firestore

        self.db = firestore.Client(project=settings.project)
        self.prefix = settings.firestore_collection_prefix
        super().__init__()
        for doc in self.db.collection(f"{self.prefix}_cases").stream():
            self.cases[doc.id] = doc.to_dict()
        for doc in self.db.collection(f"{self.prefix}_profiles").stream():
            self.profiles[doc.id] = doc.to_dict()

    def _save(self, name: str) -> None:
        super()._save(name)

    def put_case(self, case: dict) -> None:
        super().put_case(case)
        self.db.collection(f"{self.prefix}_cases").document(case["case_id"]).set(case)

    def put_profile(self, user_id: str, patch: dict) -> dict:
        prof = super().put_profile(user_id, patch)
        self.db.collection(f"{self.prefix}_profiles").document(user_id).set(prof)
        return prof

    def add_alert(self, alert: dict) -> None:
        super().add_alert(alert)
        self.db.collection(f"{self.prefix}_alerts").add(alert)


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
