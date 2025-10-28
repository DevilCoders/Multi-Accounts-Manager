"""Main window and application wiring for the Multi Accounts Manager."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QMenu,
    QAction,
)

from .data_store import Account, DataStore
from .dialogs import AccountDialog, PasswordChangeDialog

SERVICES: List[str] = [
    "Facebook",
    "Instagram",
    "Telegram",
    "Snapchat",
    "Gmail",
    "Rambler",
    "Twitter",
    "Yandex Mail",
    "Threads",
]


class ServiceTab(QWidget):
    """Widget that manages accounts for a specific service."""

    def __init__(self, service_name: str, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service_name = service_name
        self._store = store
        self._row_to_index: List[int] = []
        self._filtered_accounts: List[Account] = []

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Search username, notes or tags…")
        self._search.textChanged.connect(self.refresh)

        self._show_passwords = QCheckBox("Show passwords", self)
        self._show_passwords.toggled.connect(self.refresh)

        self._table = QTableWidget(self)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Username / Email", "Password", "Notes", "Last Updated"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_table_menu)
        self._table.itemDoubleClicked.connect(self._show_account_details)

        self._status_label = QLabel(self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        add_button = QPushButton("Add Account", self)
        add_button.clicked.connect(self._handle_add_account)
        edit_button = QPushButton("Edit Account", self)
        edit_button.clicked.connect(self._handle_edit_account)
        change_password_button = QPushButton("Change Password", self)
        change_password_button.clicked.connect(self._handle_change_password)
        delete_button = QPushButton("Delete Account", self)
        delete_button.clicked.connect(self._handle_delete_account)
        copy_username_button = QPushButton("Copy Username", self)
        copy_username_button.clicked.connect(self._copy_username)
        copy_password_button = QPushButton("Copy Password", self)
        copy_password_button.clicked.connect(self._copy_password)
        export_button = QPushButton("Export CSV", self)
        export_button.clicked.connect(self._handle_export_accounts)
        import_button = QPushButton("Import CSV", self)
        import_button.clicked.connect(self._handle_import_accounts)

        button_row = QHBoxLayout()
        for button in (
            add_button,
            edit_button,
            change_password_button,
            delete_button,
            copy_username_button,
            copy_password_button,
            export_button,
            import_button,
        ):
            button_row.addWidget(button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        search_row = QHBoxLayout()
        search_row.addWidget(self._search, stretch=2)
        search_row.addWidget(self._show_passwords)
        layout.addLayout(search_row)
        layout.addLayout(button_row)
        layout.addWidget(self._table)
        layout.addWidget(self._status_label)

        self.refresh()

    def refresh(self) -> None:
        accounts = self._store.list_accounts(self._service_name)
        query = self._search.text().strip().lower()
        filtered: List[Account] = []
        indices: List[int] = []
        for index, account in enumerate(accounts):
            haystack = " ".join(
                [
                    account.username,
                    account.notes,
                    " ".join(account.tags),
                ]
            ).lower()
            if query and query not in haystack:
                continue
            filtered.append(account)
            indices.append(index)

        self._filtered_accounts = filtered
        self._row_to_index = indices

        self._table.setRowCount(len(filtered))
        for row, account in enumerate(filtered):
            password_text = (
                account.password if self._show_passwords.isChecked() else self._mask_password(account.password)
            )
            notes_preview = account.notes.replace("\n", " ")
            if len(notes_preview) > 80:
                notes_preview = f"{notes_preview[:77]}…"

            username_item = QTableWidgetItem(account.username)
            username_item.setData(Qt.ItemDataRole.UserRole, account)
            username_item.setToolTip(
                f"Tags: {', '.join(account.tags) if account.tags else '—'}\nLast updated: {account.last_updated}"
            )
            password_item = QTableWidgetItem(password_text)
            if not self._show_passwords.isChecked():
                password_item.setToolTip("Enable 'Show passwords' to view the secret")
            else:
                password_item.setToolTip("Password copied via context menu or button")
            notes_item = QTableWidgetItem(notes_preview)
            notes_item.setToolTip(account.notes or "No notes added")
            updated_item = QTableWidgetItem(account.last_updated)

            self._table.setItem(row, 0, username_item)
            self._table.setItem(row, 1, password_item)
            self._table.setItem(row, 2, notes_item)
            self._table.setItem(row, 3, updated_item)

        total = len(accounts)
        shown = len(filtered)
        if query:
            self._status_label.setText(f"Showing {shown} of {total} account(s) (filter: '{query}')")
        else:
            self._status_label.setText(f"{total} account(s) saved")

    def _selected_row(self) -> int:
        selection = self._table.selectionModel()
        if not selection:
            return -1
        indexes = selection.selectedRows()
        if not indexes:
            return -1
        return indexes[0].row()

    def _selected_account(self) -> Account | None:
        row = self._selected_row()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if not item:
            return None
        account = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(account, Account):
            return account
        return None

    def _handle_add_account(self) -> None:
        dialog = AccountDialog(self, title=f"Add {self._service_name} Account")
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            payload = dialog.payload()
            self._store.add_account(
                self._service_name,
                Account(
                    username=payload.username,
                    password=payload.password,
                    notes=payload.notes,
                    tags=payload.tags,
                ),
            )
            self.refresh()

    def _handle_edit_account(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Edit Account", "Select an account to edit")
            return
        if row >= len(self._row_to_index):
            QMessageBox.warning(self, "Edit Account", "The selected row is no longer available.")
            return
        actual_index = self._row_to_index[row]
        account = self._store.list_accounts(self._service_name)[actual_index]
        dialog = AccountDialog(self, title=f"Edit {self._service_name} Account")
        dialog.set_initial_data(
            account.username,
            account.password,
            notes=account.notes,
            tags=account.tags,
        )
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            payload = dialog.payload()
            updated_account = account.updated(
                username=payload.username,
                password=payload.password,
                notes=payload.notes,
                tags=payload.tags,
            )
            self._store.update_account(self._service_name, actual_index, updated_account)
            self.refresh()

    def _handle_change_password(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Change Password", "Select an account first")
            return
        if row >= len(self._row_to_index):
            QMessageBox.warning(self, "Change Password", "The selected row is no longer available.")
            return
        actual_index = self._row_to_index[row]
        accounts = self._store.list_accounts(self._service_name)
        account = accounts[actual_index]
        dialog = PasswordChangeDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            new_password = dialog.password()
            updated_account = account.updated(password=new_password)
            self._store.update_account(self._service_name, actual_index, updated_account)
            self.refresh()

    def _handle_delete_account(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Delete Account", "Select an account to delete")
            return
        if row >= len(self._row_to_index):
            QMessageBox.warning(self, "Delete Account", "The selected row is no longer available.")
            return
        confirmation = QMessageBox.question(
            self,
            "Delete Account",
            "Are you sure you want to delete the selected account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            actual_index = self._row_to_index[row]
            self._store.delete_account(self._service_name, actual_index)
            self.refresh()

    @staticmethod
    def _mask_password(password: str) -> str:
        if not password:
            return ""
        return "•" * len(password)

    def _copy_username(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Copy Username", "Select an account first")
            return
        if row >= len(self._filtered_accounts):
            QMessageBox.warning(self, "Copy Username", "The selected row is no longer available.")
            return
        account = self._filtered_accounts[row]
        QApplication.clipboard().setText(account.username)
        self._status_label.setText("Username copied to clipboard")

    def _copy_password(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Copy Password", "Select an account first")
            return
        if row >= len(self._filtered_accounts):
            QMessageBox.warning(self, "Copy Password", "The selected row is no longer available.")
            return
        account = self._filtered_accounts[row]
        QApplication.clipboard().setText(account.password)
        self._status_label.setText("Password copied to clipboard")

    def _show_table_menu(self, position: QPoint) -> None:
        if not self._filtered_accounts:
            return
        menu = QMenu(self)
        copy_user = QAction("Copy Username", self)
        copy_user.triggered.connect(self._copy_username)
        copy_pass = QAction("Copy Password", self)
        copy_pass.triggered.connect(self._copy_password)
        export_action = QAction("Export to CSV", self)
        export_action.triggered.connect(self._handle_export_accounts)
        import_action = QAction("Import from CSV", self)
        import_action.triggered.connect(self._handle_import_accounts)
        menu.addAction(copy_user)
        menu.addAction(copy_pass)
        menu.addSeparator()
        menu.addAction(export_action)
        menu.addAction(import_action)
        menu.exec(self._table.viewport().mapToGlobal(position))

    def _handle_export_accounts(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self._service_name} Accounts",
            "",
            "CSV Files (*.csv)",
        )
        if not path:
            return
        count = self._store.export_service_to_csv(self._service_name, Path(path))
        QMessageBox.information(
            self,
            "Export Completed",
            f"Exported {count} account(s) for {self._service_name}.",
        )

    def _handle_import_accounts(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {self._service_name} Accounts",
            "",
            "CSV Files (*.csv)",
        )
        if not path:
            return
        added, updated = self._store.import_service_from_csv(self._service_name, Path(path))
        QMessageBox.information(
            self,
            "Import Completed",
            f"Added {added} new account(s) and updated {updated} existing ones.",
        )
        self.refresh()

    def _show_account_details(self, item: QTableWidgetItem) -> None:
        row = item.row()
        if row < 0 or row >= len(self._filtered_accounts):
            return
        account = self._filtered_accounts[row]
        password_display = (
            account.password if self._show_passwords.isChecked() else self._mask_password(account.password)
        )
        tags_display = ", ".join(account.tags) if account.tags else "—"
        message = (
            f"Username / Email: {account.username}\n"
            f"Password: {password_display}\n"
            f"Tags: {tags_display}\n"
            f"Last Updated: {account.last_updated}\n\n"
            f"Notes:\n{account.notes or '—'}"
        )
        QMessageBox.information(self, f"{self._service_name} Account", message)


class MainWindow(QMainWindow):
    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self.setWindowTitle("Multi Accounts Manager")
        self.resize(900, 600)

        self._tabs = QTabWidget(self)
        for service in SERVICES:
            tab = ServiceTab(service, self._store, self)
            self._tabs.addTab(tab, service)

        self.setCentralWidget(self._tabs)


def run_app(storage_path: Path | None = None) -> None:
    app = QApplication([])
    store = DataStore(storage_path)
    window = MainWindow(store)
    window.show()
    app.exec()
