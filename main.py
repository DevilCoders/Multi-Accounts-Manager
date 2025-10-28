"""Entry point for the Multi Accounts Manager GUI application."""

from __future__ import annotations

from pathlib import Path

from multi_accounts_manager.app import run_app


if __name__ == "__main__":
    storage_path = Path.cwd() / "accounts_data.json"
    run_app(storage_path)
