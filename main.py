"""Entry point for the Multi Accounts Manager GUI application."""

from __future__ import annotations

from pathlib import Path
import sys


def _ensure_pyqt6_available() -> None:
    """Verify that PyQt6 can be imported before starting the GUI."""

    try:
        import PyQt6.QtCore  # noqa: F401  # Imported for its side effects.
        import PyQt6.QtWidgets  # noqa: F401
    except ImportError as exc:
        message = (
            "PyQt6 is required to run the Multi Accounts Manager GUI but it "
            "could not be imported.\n"
            "Install it with `pip install PyQt6` and make sure the Qt runtime "
            "libraries are available on your system (on Windows this may "
            "require the Microsoft Visual C++ Redistributable).\n"
            f"Original error: {exc}"
        )
        raise SystemExit(message) from exc


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
    _ensure_pyqt6_available()
    from multi_accounts_manager.app import run_app

    storage_path = Path.cwd() / "accounts_data.json"
    run_app(storage_path)


if __name__ == "__main__":
    main()
