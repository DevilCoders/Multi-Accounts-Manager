"""Reusable dialogs for the Multi Accounts Manager GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

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
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from .passwords import (
    PasswordPolicy,
    PasswordStrength,
    estimate_password_strength,
    generate_password,
)


@dataclass
class AccountPayload:
    username: str
    password: str
    notes: str
    tags: List[str]


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
        self._confirm_password = QLineEdit(self)
        self._confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._show_password = QCheckBox("Show password", self)
        self._show_password.toggled.connect(self._toggle_password_visibility)
        self._notes = QPlainTextEdit(self)
        self._notes.setPlaceholderText("Optional notes, URLs or security questions…")
        self._notes.setMinimumHeight(60)
        self._tags = QLineEdit(self)
        self._tags.setPlaceholderText("Comma separated e.g. personal, backup")
        self._strength_label = QLabel("Not analysed", self)
        self._strength_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        form = QFormLayout()
        form.addRow("Username / Email", self._username)

        password_row = QHBoxLayout()
        password_row.addWidget(self._password, stretch=1)
        generator_button = QPushButton("Generate", self)
        generator_button.clicked.connect(self._handle_generate_password)
        password_row.addWidget(generator_button)
        form.addRow("Password", password_row)
        form.addRow("Confirm Password", self._confirm_password)
        form.addRow("Password Strength", self._strength_label)
        form.addRow("", self._show_password)
        form.addRow("Tags", self._tags)
        form.addRow("Notes", self._notes)

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

        self._password.textChanged.connect(self._update_strength)
        self._confirm_password.textChanged.connect(self._sync_strength_state)

    def set_initial_data(
        self, username: str, password: str, *, notes: str = "", tags: List[str] | None = None
    ) -> None:
        self._username.setText(username)
        self._password.setText(password)
        self._confirm_password.setText(password)
        self._update_strength(password)
        self._notes.setPlainText(notes)
        self._tags.setText(", ".join(tags or []))

    def payload(self) -> AccountPayload:
        return AccountPayload(
            username=self._username.text().strip(),
            password=self._password.text(),
            notes=self._notes.toPlainText().strip(),
            tags=_split_tags(self._tags.text()),
        )

    def _handle_generate_password(self) -> None:
        policy_dialog = PasswordGeneratorDialog(self)
        if policy_dialog.exec() == int(QDialog.DialogCode.Accepted):
            self._password.setText(policy_dialog.generated_password)
            self._confirm_password.setText(policy_dialog.generated_password)

    def _handle_accept(self) -> None:
        payload = self.payload()
        if not payload.username:
            QMessageBox.warning(self, "Validation", "Username / Email is required")
            return
        if not payload.password:
            QMessageBox.warning(self, "Validation", "Password is required")
            return
        if payload.password != self._confirm_password.text():
            QMessageBox.warning(self, "Validation", "Passwords do not match")
            return
        self.accept()

    def _update_strength(self, password: str) -> None:
        strength = estimate_password_strength(password)
        self._display_strength(strength)

    def _sync_strength_state(self) -> None:
        # Triggered to ensure the strength label updates if password cleared via confirm field
        self._update_strength(self._password.text())

    def _display_strength(self, strength: PasswordStrength) -> None:
        self._strength_label.setText(f"{strength.label} (score {strength.score}/4)")
        self._strength_label.setStyleSheet(f"color: {strength.color};")
        if strength.suggestions:
            self._strength_label.setToolTip("\n".join(strength.suggestions))
        else:
            self._strength_label.setToolTip("")

    def _toggle_password_visibility(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._password.setEchoMode(mode)
        self._confirm_password.setEchoMode(mode)


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
        self._confirm = QLineEdit(self)
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._show_password = QCheckBox("Show password", self)
        self._show_password.toggled.connect(self._toggle_visibility)
        self._strength_label = QLabel("Not analysed", self)
        self._strength_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        generate_button = QPushButton("Generate", self)
        generate_button.clicked.connect(self._handle_generate_password)

        password_row = QHBoxLayout()
        password_row.addWidget(self._password)
        password_row.addWidget(generate_button)

        form = QFormLayout(self)
        form.addRow("New Password", password_row)
        form.addRow("Confirm Password", self._confirm)
        form.addRow("Password Strength", self._strength_label)
        form.addRow("", self._show_password)

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

        self._password.textChanged.connect(self._update_strength)
        self._confirm.textChanged.connect(self._sync_strength)

    def password(self) -> str:
        return self._password.text()

    def _handle_generate_password(self) -> None:
        policy_dialog = PasswordGeneratorDialog(self)
        if policy_dialog.exec() == int(QDialog.DialogCode.Accepted):
            self._password.setText(policy_dialog.generated_password)
            self._confirm.setText(policy_dialog.generated_password)

    def _handle_accept(self) -> None:
        if not self.password():
            QMessageBox.warning(self, "Validation", "Password must not be empty")
            return
        if self.password() != self._confirm.text():
            QMessageBox.warning(self, "Validation", "Passwords do not match")
            return
        self.accept()

    def _update_strength(self, password: str) -> None:
        strength = estimate_password_strength(password)
        self._strength_label.setText(f"{strength.label} (score {strength.score}/4)")
        self._strength_label.setStyleSheet(f"color: {strength.color};")
        if strength.suggestions:
            self._strength_label.setToolTip("\n".join(strength.suggestions))
        else:
            self._strength_label.setToolTip("")

    def _sync_strength(self) -> None:
        self._update_strength(self._password.text())

    def _toggle_visibility(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._password.setEchoMode(mode)
        self._confirm.setEchoMode(mode)


def _split_tags(raw: str) -> List[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]
