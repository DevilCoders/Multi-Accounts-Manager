"""Persistence helpers for the Multi Accounts Manager application."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

DEFAULT_DATA_FILE = Path.home() / ".multi_accounts_manager.json"


@dataclass
class Account:
    """Representation of a single stored account."""

    username: str
    password: str


@dataclass
class ServiceData:
    """Container for accounts that belong to a specific service."""

    name: str
    accounts: List[Account] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        return {"name": self.name, "accounts": [account.__dict__ for account in self.accounts]}

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "ServiceData":
        accounts = [Account(**entry) for entry in payload.get("accounts", [])]
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

        serialised = {
            name: {"accounts": [account.__dict__ for account in service.accounts]}
            for name, service in self._services.items()
        }
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
