"""Reusable dialogs for the Multi Accounts Manager GUI."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QWidget,
)

from .passwords import PasswordPolicy, generate_password


@dataclass
class AccountPayload:
    username: str
    password: str


class AccountDialog(QDialog):
    """Dialog used for creating or editing an account."""

    def __init__(self, parent: QWidget | None = None, *, title: str = "Account") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 150)

        self._username = QLineEdit(self)
        self._password = QLineEdit(self)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Username / Email", self._username)

        password_row = QHBoxLayout()
        password_row.addWidget(self._password, stretch=1)
        generator_button = QPushButton("Generate", self)
        generator_button.clicked.connect(self._handle_generate_password)
        password_row.addWidget(generator_button)
        form.addRow("Password", password_row)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        self._buttons.accepted.connect(self._handle_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(self._buttons)

    def set_initial_data(self, username: str, password: str) -> None:
        self._username.setText(username)
        self._password.setText(password)

    def payload(self) -> AccountPayload:
        return AccountPayload(username=self._username.text().strip(), password=self._password.text())

    def _handle_generate_password(self) -> None:
        policy_dialog = PasswordGeneratorDialog(self)
        if policy_dialog.exec() == int(QDialog.DialogCode.Accepted):
            self._password.setText(policy_dialog.generated_password)

    def _handle_accept(self) -> None:
        payload = self.payload()
        if not payload.username:
            QMessageBox.warning(self, "Validation", "Username / Email is required")
            return
        if not payload.password:
            QMessageBox.warning(self, "Validation", "Password is required")
            return
        self.accept()


class PasswordGeneratorDialog(QDialog):
    """Dialog that lets the user customise password generation settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.generated_password = ""

        self._length = QSpinBox(self)
        self._length.setRange(6, 128)
        self._length.setValue(16)

        self._use_lower = QCheckBox("Include lowercase", self)
        self._use_lower.setChecked(True)
        self._use_upper = QCheckBox("Include uppercase", self)
        self._use_upper.setChecked(True)
        self._use_digits = QCheckBox("Include digits", self)
        self._use_digits.setChecked(True)
        self._use_symbols = QCheckBox("Include symbols", self)
        self._use_symbols.setChecked(True)

        form = QFormLayout()
        form.addRow("Length", self._length)
        form.addRow(self._use_lower)
        form.addRow(self._use_upper)
        form.addRow(self._use_digits)
        form.addRow(self._use_symbols)

        self._password_display = QLineEdit(self)
        self._password_display.setReadOnly(True)
        form.addRow(QLabel("Generated Password", self))
        form.addRow(self._password_display)

        generate_button = QPushButton("Generate", self)
        generate_button.clicked.connect(self._generate)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        wrapper = QFormLayout(self)
        wrapper.addRow(form)
        wrapper.addRow(generate_button)
        wrapper.addRow(buttons)

        self._buttons = buttons

    def _generate(self) -> None:
        policy = PasswordPolicy(
            length=self._length.value(),
            use_lowercase=self._use_lower.isChecked(),
            use_uppercase=self._use_upper.isChecked(),
            use_digits=self._use_digits.isChecked(),
            use_symbols=self._use_symbols.isChecked(),
        )
        try:
            password = generate_password(policy)
        except ValueError as exc:
            QMessageBox.warning(self, "Password Generator", str(exc))
            return
        self.generated_password = password
        self._password_display.setText(password)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)


class PasswordChangeDialog(QDialog):
    """Dialog used specifically for changing a password of an account."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self._password = QLineEdit(self)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        generate_button = QPushButton("Generate", self)
        generate_button.clicked.connect(self._handle_generate_password)

        password_row = QHBoxLayout()
        password_row.addWidget(self._password)
        password_row.addWidget(generate_button)

        form = QFormLayout(self)
        form.addRow("New Password", password_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self._handle_accept)
        buttons.rejected.connect(self.reject)

        wrapper = QFormLayout(self)
        wrapper.addRow(form)
        wrapper.addRow(buttons)

    def password(self) -> str:
        return self._password.text()

    def _handle_generate_password(self) -> None:
        policy_dialog = PasswordGeneratorDialog(self)
        if policy_dialog.exec() == int(QDialog.DialogCode.Accepted):
            self._password.setText(policy_dialog.generated_password)

    def _handle_accept(self) -> None:
        if not self.password():
            QMessageBox.warning(self, "Validation", "Password must not be empty")
            return
        self.accept()
