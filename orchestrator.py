"""
Backup Orchestrator -- Centralized backup management for go_backup agents.

Entry point for the PySide6 GUI application.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor

from gui.models.database import OrchestratorDatabase
from gui.models.credential_store import CredentialStore
from gui.main_window import MainWindow


DATA_DIR = PROJECT_ROOT / "data"


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BackupOrchestrator")
    app.setOrganizationName("daPaz")

    # Force light colour scheme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#F5F6FA"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#1A1A2E"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F9FAFB"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#1A1A2E"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1A1A2E"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1F3864"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9CA3AF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1F3864"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    app.setPalette(palette)

    app.setFont(QFont("Segoe UI", 10))

    app.setStyleSheet("""
        QToolTip {
            background-color: #1F3864;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 9pt;
        }
        QScrollBar:vertical {
            background: #F5F6FA;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #94A3B8;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
    """)

    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    # Initialize database
    db = OrchestratorDatabase(DATA_DIR / "orchestrator.db")

    # Initialize credential store
    cred_store = CredentialStore(DATA_DIR / "credentials.db")

    # Master password dialog
    if not _unlock_credential_store(app, cred_store):
        sys.exit(0)

    window = MainWindow(db, credential_store=cred_store)
    window.show()

    sys.exit(app.exec())


def _unlock_credential_store(app: QApplication, cred_store: CredentialStore) -> bool:
    """Prompt for master password and unlock the credential store."""
    is_new = cred_store.is_new()

    if is_new:
        # First run: set master password
        password, ok = QInputDialog.getText(
            None,
            "Set Master Password",
            "Create a master password to protect backup credentials.\n"
            "This password will be required each time you start the orchestrator.",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not password:
            return False

        confirm, ok = QInputDialog.getText(
            None, "Confirm Master Password",
            "Confirm your master password:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or confirm != password:
            QMessageBox.warning(None, "Mismatch", "Passwords do not match.")
            return False

        return cred_store.unlock(password)
    else:
        # Existing store: unlock
        for attempt in range(3):
            password, ok = QInputDialog.getText(
                None, "Master Password",
                "Enter master password to unlock credential store:",
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                return False
            if cred_store.unlock(password):
                return True
            QMessageBox.warning(
                None, "Incorrect",
                f"Wrong password. {2 - attempt} attempt(s) remaining.",
            )
        return False


if __name__ == "__main__":
    main()
