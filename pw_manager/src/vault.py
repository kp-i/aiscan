"""
Vault data model. All data is stored as a JSON dict and persisted as
an AES-256-GCM encrypted binary file.

Schema:
{
  "version": 1,
  "entries": [
    {
      "id": "<uuid>",
      "title": "GitHub",
      "url": "https://github.com",
      "username": "alice",
      "password": "s3cr3t",
      "category": "開発",
      "tags": ["git", "work"],
      "notes": "2FA enabled",
      "created_at": "2026-02-25T00:00:00",
      "updated_at": "2026-02-25T00:00:00"
    }
  ]
}
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.crypto import encrypt, decrypt

DEFAULT_CATEGORIES = [
    "仕事", "プライベート", "開発", "金融", "SNS", "ショッピング", "その他"
]


class Entry:
    def __init__(
        self,
        title: str,
        url: str = "",
        username: str = "",
        password: str = "",
        category: str = "その他",
        tags: Optional[List[str]] = None,
        notes: str = "",
        entry_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.id = entry_id or str(uuid.uuid4())
        self.title = title
        self.url = url
        self.username = username
        self.password = password
        self.category = category
        self.tags = tags or []
        self.notes = notes
        now = datetime.now().isoformat(timespec="seconds")
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def touch(self):
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "category": self.category,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Entry":
        return cls(
            title=d.get("title", ""),
            url=d.get("url", ""),
            username=d.get("username", ""),
            password=d.get("password", ""),
            category=d.get("category", "その他"),
            tags=d.get("tags", []),
            notes=d.get("notes", ""),
            entry_id=d.get("id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


class Vault:
    VERSION = 1

    def __init__(self):
        self.entries: List[Entry] = []
        self._password: Optional[str] = None
        self._path: Optional[Path] = None

    # ── persistence ──────────────────────────────────────────────

    def new(self, path: Path, password: str):
        """Create a brand-new empty vault."""
        self._path = path
        self._password = password
        self.entries = []
        self.save()

    def load(self, path: Path, password: str):
        """Load & decrypt an existing vault file."""
        raw = path.read_bytes()
        plaintext = decrypt(raw, password)
        data = json.loads(plaintext.decode("utf-8"))
        self.entries = [Entry.from_dict(e) for e in data.get("entries", [])]
        self._password = password
        self._path = path

    def save(self):
        """Encrypt & write the vault to disk."""
        if self._path is None or self._password is None:
            raise RuntimeError("Vault is not initialised.")
        data = {"version": self.VERSION, "entries": [e.to_dict() for e in self.entries]}
        plaintext = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self._path.write_bytes(encrypt(plaintext, self._password))

    def export_to(self, path: Path, password: Optional[str] = None):
        """Export vault to a different file (optionally with a new password)."""
        export_password = password or self._password
        data = {"version": self.VERSION, "entries": [e.to_dict() for e in self.entries]}
        plaintext = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        path.write_bytes(encrypt(plaintext, export_password))

    def change_password(self, new_password: str):
        self._password = new_password
        self.save()

    # ── CRUD ─────────────────────────────────────────────────────

    def add(self, entry: Entry):
        self.entries.append(entry)
        self.save()

    def update(self, entry: Entry):
        for i, e in enumerate(self.entries):
            if e.id == entry.id:
                entry.touch()
                self.entries[i] = entry
                self.save()
                return
        raise KeyError(f"Entry {entry.id} not found.")

    def delete(self, entry_id: str):
        self.entries = [e for e in self.entries if e.id != entry_id]
        self.save()

    def get(self, entry_id: str) -> Optional[Entry]:
        return next((e for e in self.entries if e.id == entry_id), None)

    # ── search / filter ──────────────────────────────────────────

    def search(self, query: str, category: str = "") -> List[Entry]:
        q = query.lower()
        results = self.entries
        if category and category != "すべて":
            results = [e for e in results if e.category == category]
        if q:
            results = [
                e for e in results
                if q in e.title.lower()
                or q in e.url.lower()
                or q in e.username.lower()
                or q in " ".join(e.tags).lower()
                or q in e.notes.lower()
            ]
        return results

    def categories(self) -> List[str]:
        used = sorted({e.category for e in self.entries})
        return used
