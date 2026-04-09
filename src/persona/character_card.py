"""Character card system for persona customization."""

import base64
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import qrcode

logger = logging.getLogger(__name__)


@dataclass
class CharacterCard:
    """A character card for persona customization."""

    id: str
    name: str
    description: str
    personality: str
    background: str
    greeting: str
    example_dialogues: list[dict[str, str]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    avatar: str | None = None
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "background": self.background,
            "greeting": self.greeting,
            "example_dialogues": self.example_dialogues,
            "tags": self.tags,
            "avatar": self.avatar,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CharacterCard":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            personality=data.get("personality", ""),
            background=data.get("background", ""),
            greeting=data.get("greeting", ""),
            example_dialogues=data.get("example_dialogues", []),
            tags=data.get("tags", []),
            avatar=data.get("avatar"),
            system_prompt=data.get("system_prompt", ""),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2048),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )

    def build_system_prompt(self) -> str:
        """Build the system prompt for this character."""
        parts = []

        if self.system_prompt:
            parts.append(self.system_prompt)
        else:
            if self.description:
                parts.append(f"You are {self.name}. {self.description}")
            if self.personality:
                parts.append(f"Personality: {self.personality}")
            if self.background:
                parts.append(f"Background: {self.background}")

        if self.example_dialogues:
            parts.append("\nExample dialogues:")
            for dialogue in self.example_dialogues[:5]:
                user_msg = dialogue.get("user", "")
                assistant_msg = dialogue.get("assistant", "")
                parts.append(f"User: {user_msg}")
                parts.append(f"{self.name}: {assistant_msg}")

        return "\n\n".join(parts)

    def generate_qr_code(self, url: str | None = None) -> str:
        """Generate a QR code for sharing this character card."""
        if url is None:
            card_data = json.dumps(self.to_dict(), ensure_ascii=False)
            url = f"pyagent://character?data={base64.urlsafe_b64encode(card_data.encode()).decode()}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()


class CharacterCardManager:
    """Manager for character cards."""

    def __init__(self, storage_path: str = "data/characters"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._cards: dict[str, CharacterCard] = {}
        self._load_all()

    def _load_all(self) -> None:
        for card_file in self._storage_path.glob("*.json"):
            try:
                with open(card_file, encoding="utf-8") as f:
                    data = json.load(f)
                    card = CharacterCard.from_dict(data)
                    self._cards[card.id] = card
            except Exception as e:
                logger.warning("Failed to load character card %s: %s", card_file, e)

    def create_card(
        self,
        name: str,
        description: str = "",
        personality: str = "",
        background: str = "",
        greeting: str = "",
        **kwargs: Any,
    ) -> CharacterCard:
        import uuid

        card = CharacterCard(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            personality=personality,
            background=background,
            greeting=greeting,
            **kwargs,
        )
        self._cards[card.id] = card
        self._save_card(card)
        logger.info("Created character card: %s", name)
        return card

    def update_card(self, card_id: str, **kwargs: Any) -> CharacterCard | None:
        card = self._cards.get(card_id)
        if not card:
            return None

        for key, value in kwargs.items():
            if hasattr(card, key):
                setattr(card, key, value)
        card.updated_at = datetime.now()

        self._save_card(card)
        return card

    def delete_card(self, card_id: str) -> bool:
        card = self._cards.get(card_id)
        if not card:
            return False

        card_file = self._storage_path / f"{card_id}.json"
        if card_file.exists():
            card_file.unlink()

        del self._cards[card_id]
        return True

    def get_card(self, card_id: str) -> CharacterCard | None:
        return self._cards.get(card_id)

    def list_cards(self, tags: list[str] | None = None) -> list[CharacterCard]:
        cards = list(self._cards.values())
        if tags:
            cards = [c for c in cards if any(tag in c.tags for tag in tags)]
        return cards

    def import_card(self, data: dict[str, Any] | str) -> CharacterCard:
        if isinstance(data, str):
            if data.startswith("pyagent://character?data="):
                encoded = data.split("data=")[1]
                json_str = base64.urlsafe_b64decode(encoded).decode()
                data = json.loads(json_str)
            else:
                data = json.loads(data)

        card = CharacterCard.from_dict(data)
        self._cards[card.id] = card
        self._save_card(card)
        return card

    def export_card(self, card_id: str) -> str:
        card = self._cards.get(card_id)
        if not card:
            raise ValueError(f"Card not found: {card_id}")
        return json.dumps(card.to_dict(), ensure_ascii=False, indent=2)

    def _save_card(self, card: CharacterCard) -> None:
        card_file = self._storage_path / f"{card.id}.json"
        with open(card_file, "w", encoding="utf-8") as f:
            json.dump(card.to_dict(), f, ensure_ascii=False, indent=2)


_manager: CharacterCardManager | None = None


def get_character_card_manager() -> CharacterCardManager:
    global _manager
    if _manager is None:
        _manager = CharacterCardManager()
    return _manager
