"""Entry point for the Multi Accounts Manager GUI application."""

from __future__ import annotations

from pathlib import Path
import sys


def _ensure_project_on_path() -> None:
    """Ensure the project root is available on ``sys.path``.

    Some execution environments (for example, when the script is launched from
    a directory that is not the repository root) might not automatically add
    the project directory to ``sys.path``.  This helper explicitly inserts the
    directory containing ``main.py`` so that ``multi_accounts_manager`` can be
    imported reliably.
    """

    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def main() -> None:
    """Launch the GUI application."""

    _ensure_project_on_path()
    from multi_accounts_manager.app import run_app

    storage_path = Path.cwd() / "accounts_data.json"
    run_app(storage_path)


if __name__ == "__main__":
    main()
