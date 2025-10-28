"""Main window and application wiring for the Multi Accounts Manager."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
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

        self._table = QTableWidget(self)
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Username / Email", "Password"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

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

        button_row = QHBoxLayout()
        for button in (add_button, edit_button, change_password_button, delete_button):
            button_row.addWidget(button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(self._table)
        layout.addWidget(self._status_label)

        self.refresh()

    def refresh(self) -> None:
        accounts = self._store.list_accounts(self._service_name)
        self._table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            username_item = QTableWidgetItem(account.username)
            password_item = QTableWidgetItem(self._mask_password(account.password))
            username_item.setData(Qt.ItemDataRole.UserRole, account)
            self._table.setItem(row, 0, username_item)
            self._table.setItem(row, 1, password_item)
        self._status_label.setText(f"{len(accounts)} account(s) saved")

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
                Account(username=payload.username, password=payload.password),
            )
            self.refresh()

    def _handle_edit_account(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Edit Account", "Select an account to edit")
            return
        account = self._store.list_accounts(self._service_name)[row]
        dialog = AccountDialog(self, title=f"Edit {self._service_name} Account")
        dialog.set_initial_data(account.username, account.password)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            payload = dialog.payload()
            self._store.update_account(
                self._service_name,
                row,
                Account(username=payload.username, password=payload.password),
            )
            self.refresh()

    def _handle_change_password(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Change Password", "Select an account first")
            return
        accounts = self._store.list_accounts(self._service_name)
        account = accounts[row]
        dialog = PasswordChangeDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            new_password = dialog.password()
            self._store.update_account(
                self._service_name,
                row,
                Account(username=account.username, password=new_password),
            )
            self.refresh()

    def _handle_delete_account(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Delete Account", "Select an account to delete")
            return
        confirmation = QMessageBox.question(
            self,
            "Delete Account",
            "Are you sure you want to delete the selected account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            self._store.delete_account(self._service_name, row)
            self.refresh()

    @staticmethod
    def _mask_password(password: str) -> str:
        if not password:
            return ""
        return "•" * len(password)


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
