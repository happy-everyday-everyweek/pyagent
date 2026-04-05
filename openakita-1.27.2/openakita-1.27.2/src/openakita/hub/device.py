"""
Device identity management.

Generates and persists a random UUID as a stable device identifier.
No hardware fingerprinting — simple, privacy-friendly, sufficient for dedup.
"""

import json
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_DEVICE_FILE = "device.json"


def get_or_create_device_id(data_dir: Path) -> str:
    """Return the device_id, creating one on first run.

    The ID is a 16-character hex string persisted in ``data_dir/device.json``.
    """
    fp = data_dir / _DEVICE_FILE
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            did = data.get("device_id", "")
            if did:
                return did
        except Exception:
            logger.warning("Corrupt device.json — regenerating device_id")

    did = uuid.uuid4().hex[:16]
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps({"device_id": did}, indent=2), encoding="utf-8")
    logger.info("Generated new device_id: %s", did)
    return did
