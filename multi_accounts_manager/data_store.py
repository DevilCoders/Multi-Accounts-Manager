"""Persistence helpers for the Multi Accounts Manager application."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

DEFAULT_DATA_FILE = Path.home() / ".multi_accounts_manager.json"


@dataclass
class Account:
    """Representation of a single stored account."""

    username: str
    password: str
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: _now())

    def __post_init__(self) -> None:
        self.tags = _normalise_tags(self.tags)

    def to_dict(self) -> Dict[str, object]:
        return {
            "username": self.username,
            "password": self.password,
            "notes": self.notes,
            "tags": self.tags,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Account":
        username = str(payload.get("username", ""))
        password = str(payload.get("password", ""))
        notes = str(payload.get("notes", ""))
        raw_tags = payload.get("tags", [])
        if isinstance(raw_tags, str):
            tags: Iterable[str] = raw_tags.split(",")
        elif isinstance(raw_tags, Iterable):
            tags = raw_tags
        else:
            tags = []
        last_updated = str(payload.get("last_updated", _now()))
        return cls(
            username=username,
            password=password,
            notes=notes,
            tags=list(tags),
            last_updated=last_updated,
        )

    def updated(self, **changes: object) -> "Account":
        """Return a copy of the account with new values applied."""

        allowed = {k: v for k, v in changes.items() if v is not None}
        if "tags" in allowed:
            allowed["tags"] = _normalise_tags(allowed["tags"])
        updated = replace(self, **allowed)
        return replace(updated, last_updated=_now())


@dataclass
class ServiceData:
    """Container for accounts that belong to a specific service."""

    name: str
    accounts: List[Account] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[Dict[str, object]]]:
        return {"name": self.name, "accounts": [account.to_dict() for account in self.accounts]}

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "ServiceData":
        raw_accounts = payload.get("accounts", [])
        accounts = [Account.from_dict(entry) for entry in raw_accounts if isinstance(entry, dict)]
        return cls(name=str(payload.get("name", "")), accounts=accounts)


class DataStore:
    """Simple JSON-based persistence layer for account data."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path = Path(storage_path or DEFAULT_DATA_FILE)
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._services: Dict[str, ServiceData] = {}
        self.load()

    @property
    def storage_path(self) -> Path:
        return self._storage_path

    def load(self) -> None:
        if not self._storage_path.exists():
            self._services = {}
            return
        try:
            import json

            with self._storage_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError):
            self._services = {}
            return

        services: Dict[str, ServiceData] = {}
        for name, raw_data in payload.items():
            if isinstance(raw_data, dict):
                services[name] = ServiceData.from_dict({"name": name, **raw_data})
        self._services = services

    def save(self) -> None:
        import json

        serialised = {name: {"accounts": [account.to_dict() for account in service.accounts]} for name, service in self._services.items()}
        with self._storage_path.open("w", encoding="utf-8") as handle:
            json.dump(serialised, handle, indent=2)

    def get_service(self, service_name: str) -> ServiceData:
        if service_name not in self._services:
            self._services[service_name] = ServiceData(name=service_name)
        return self._services[service_name]

    def set_accounts(self, service_name: str, accounts: List[Account]) -> None:
        self._services[service_name] = ServiceData(name=service_name, accounts=accounts)
        self.save()

    def add_account(self, service_name: str, account: Account) -> None:
        service = self.get_service(service_name)
        service.accounts.append(account)
        self.save()

    def update_account(self, service_name: str, index: int, account: Account) -> None:
        service = self.get_service(service_name)
        if 0 <= index < len(service.accounts):
            service.accounts[index] = account
            self.save()

    def delete_account(self, service_name: str, index: int) -> None:
        service = self.get_service(service_name)
        if 0 <= index < len(service.accounts):
            del service.accounts[index]
            self.save()

    def list_accounts(self, service_name: str) -> List[Account]:
        return list(self.get_service(service_name).accounts)

    def all_services(self) -> Dict[str, ServiceData]:
        return self._services.copy()

    # --- Export & import helpers -------------------------------------------------

    def export_service_to_csv(self, service_name: str, destination: Path) -> int:
        """Export the selected service accounts to a CSV file.

        Returns the number of accounts written.
        """

        import csv

        accounts = self.list_accounts(service_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["username", "password", "notes", "tags", "last_updated"],
            )
            writer.writeheader()
            for account in accounts:
                payload = account.to_dict()
                payload["tags"] = ", ".join(account.tags)
                writer.writerow(payload)
        return len(accounts)

    def import_service_from_csv(self, service_name: str, source: Path) -> Tuple[int, int]:
        """Import accounts from a CSV file.

        Returns a tuple ``(added, updated)`` describing the number of new and
        replaced entries.
        """

        import csv

        existing = self.get_service(service_name)
        seen = {account.username: idx for idx, account in enumerate(existing.accounts)}
        added = updated = 0
        with source.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                account = Account.from_dict(row)
                if account.username in seen:
                    index = seen[account.username]
                    existing.accounts[index] = existing.accounts[index].updated(
                        password=account.password,
                        notes=account.notes,
                        tags=account.tags,
                    )
                    updated += 1
                else:
                    existing.accounts.append(account)
                    seen[account.username] = len(existing.accounts) - 1
                    added += 1
        self.save()
        return added, updated


def _normalise_tags(tags: Iterable[str]) -> List[str]:
    cleaned = []
    for tag in tags:
        stripped = str(tag).strip()
        if stripped and stripped not in cleaned:
            cleaned.append(stripped)
    return cleaned


def _now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")
