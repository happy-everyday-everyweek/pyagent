"""Virtual key management for secure API key handling."""

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VirtualKey:
    key_id: str
    key_hash: str
    name: str
    provider: str
    permissions: list[str] = field(default_factory=list)
    rate_limit: int = 100
    daily_limit: float | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: datetime | None = None
    usage_count: int = 0
    daily_usage: float = 0.0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "name": self.name,
            "provider": self.provider,
            "permissions": self.permissions,
            "rate_limit": self.rate_limit,
            "daily_limit": self.daily_limit,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "daily_usage": self.daily_usage,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


class KeyManager:
    def __init__(self, storage_path: str = "data/keys", secret_key: str | None = None):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._secret_key = secret_key or secrets.token_hex(32)
        self._keys: dict[str, VirtualKey] = {}
        self._key_mappings: dict[str, str] = {}
        self._load_keys()

    def _load_keys(self) -> None:
        filepath = self._storage_path / "keys.json"
        if not filepath.exists():
            return

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        for key_data in data.get("keys", []):
            key = VirtualKey(
                key_id=key_data["key_id"],
                key_hash=key_data["key_hash"],
                name=key_data["name"],
                provider=key_data["provider"],
                permissions=key_data.get("permissions", []),
                rate_limit=key_data.get("rate_limit", 100),
                daily_limit=key_data.get("daily_limit"),
                expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data.get("expires_at") else None,
                created_at=datetime.fromisoformat(key_data["created_at"]),
                last_used_at=datetime.fromisoformat(key_data["last_used_at"]) if key_data.get("last_used_at") else None,
                usage_count=key_data.get("usage_count", 0),
                daily_usage=key_data.get("daily_usage", 0.0),
                enabled=key_data.get("enabled", True),
                metadata=key_data.get("metadata", {}),
            )
            self._keys[key.key_id] = key

    def _save_keys(self) -> None:
        filepath = self._storage_path / "keys.json"
        data = {"keys": [k.to_dict() for k in self._keys.values()]}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_key(
        self,
        name: str,
        provider: str,
        permissions: list[str] | None = None,
        rate_limit: int = 100,
        daily_limit: float | None = None,
        expires_in_days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, VirtualKey]:
        key_id = f"pk_{secrets.token_hex(8)}"
        raw_key = secrets.token_urlsafe(32)
        key_hash = self._hash_key(raw_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        virtual_key = VirtualKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            provider=provider,
            permissions=permissions or ["*"],
            rate_limit=rate_limit,
            daily_limit=daily_limit,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self._keys[key_id] = virtual_key
        self._key_mappings[key_hash] = key_id
        self._save_keys()

        logger.info("Generated virtual key: %s for provider: %s", key_id, provider)
        return f"{key_id}.{raw_key}", virtual_key

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(f"{self._secret_key}:{raw_key}".encode()).hexdigest()

    def validate_key(self, full_key: str) -> VirtualKey | None:
        try:
            key_id, raw_key = full_key.split(".", 1)
        except ValueError:
            return None

        key = self._keys.get(key_id)
        if not key:
            return None

        if not key.enabled:
            return None

        if key.expires_at and datetime.now() > key.expires_at:
            return None

        expected_hash = self._hash_key(raw_key)
        if not hmac.compare_digest(key.key_hash, expected_hash):
            return None

        key.last_used_at = datetime.now()
        key.usage_count += 1
        self._save_keys()

        return key

    def check_permission(self, key: VirtualKey, permission: str) -> bool:
        if "*" in key.permissions:
            return True
        return permission in key.permissions

    def check_rate_limit(self, key: VirtualKey) -> bool:
        return key.usage_count < key.rate_limit

    def check_daily_limit(self, key: VirtualKey, cost: float) -> bool:
        if key.daily_limit is None:
            return True
        return key.daily_usage + cost <= key.daily_limit

    def record_usage(self, key_id: str, cost: float) -> None:
        key = self._keys.get(key_id)
        if key:
            key.daily_usage += cost
            self._save_keys()

    def revoke_key(self, key_id: str) -> bool:
        if key_id not in self._keys:
            return False

        key = self._keys[key_id]
        key.enabled = False
        self._save_keys()

        logger.info("Revoked virtual key: %s", key_id)
        return True

    def delete_key(self, key_id: str) -> bool:
        if key_id not in self._keys:
            return False

        key = self._keys[key_id]
        if key.key_hash in self._key_mappings:
            del self._key_mappings[key.key_hash]

        del self._keys[key_id]
        self._save_keys()

        logger.info("Deleted virtual key: %s", key_id)
        return True

    def get_key(self, key_id: str) -> VirtualKey | None:
        return self._keys.get(key_id)

    def list_keys(self, provider: str | None = None) -> list[VirtualKey]:
        keys = list(self._keys.values())
        if provider:
            keys = [k for k in keys if k.provider == provider]
        return keys

    def rotate_key(self, key_id: str) -> tuple[str, VirtualKey] | None:
        key = self._keys.get(key_id)
        if not key:
            return None

        raw_key = secrets.token_urlsafe(32)
        key.key_hash = self._hash_key(raw_key)
        key.usage_count = 0
        key.daily_usage = 0.0
        self._save_keys()

        logger.info("Rotated virtual key: %s", key_id)
        return f"{key_id}.{raw_key}", key


_manager: KeyManager | None = None


def get_key_manager() -> KeyManager:
    global _manager
    if _manager is None:
        _manager = KeyManager()
    return _manager
