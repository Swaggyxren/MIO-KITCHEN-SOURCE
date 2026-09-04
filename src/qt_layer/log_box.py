import time
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit


class OperationLogsWidget(QWidget):
    """
    Operation Logs Area matching the exact design from new_ui_prototype.html:
    - Top header bar with 'Operation Logs' title and 'Clear' button
    - Cascadia Code / Monospace text edit
    - Real-time logging with timestamps
    - Solid dark background (#1a1a1a) with border (#2d2d2d)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OperationLogsWidget")
        self.setFixedWidth(280)
        self.initUI()
        self.init_welcome_logs()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header Bar (34px height, #222222 background, #2d2d2d bottom border)
        header = QWidget(self)
        header.setFixedHeight(34)
        header.setStyleSheet("""
            QWidget {
                background-color: #222222;
                border-bottom: 1px solid #2d2d2d;
                border-right: 1px solid #2d2d2d;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 10, 0)

        title_lbl = QLabel("Operation Logs", header)
        title_lbl.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        self.clear_btn = QPushButton("Clear", header)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                color: #888888;
                font-size: 11px;
                border: none;
                background: transparent;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_btn)

        layout.addWidget(header)

        # 2. Log Display Area (#1a1a1a background, monospace font)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #cccccc;
                border: none;
                border-right: 1px solid #2d2d2d;
                font-family: 'Cascadia Code', Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #444444;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        layout.addWidget(self.text_edit, 1)

        self._formats = {
            "INFO": self._create_format(QColor("#2ECC71")),
            "WARN": self._create_format(QColor("#F1C40F")),
            "ERROR": self._create_format(QColor("#E74C3C")),
            "DEBUG": self._create_format(QColor("#888888")),
            "MUTED": self._create_format(QColor("#666666")),
            "TIME": self._create_format(QColor("#666666")),
            "TEXT": self._create_format(QColor("#cccccc")),
        }

    def _create_format(self, color: QColor) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        return fmt

    def init_welcome_logs(self):
        t = time.strftime("%H:%M:%S")
        self.append_log(f"[{t}] Engine initialized", "MUTED")
        self.append_log(f"[{t}] System ready", "DEBUG")
        self.append_log(f"[{t}] Ready", "INFO")

    def clear_logs(self):
        self.text_edit.clear()

    @Slot(str)
    def append_text(self, text: str):
        """Append raw line from stdout/stderr or internal log"""
        clean_text = text.rstrip('\r\n')
        if not clean_text:
            return
        t = time.strftime("%H:%M:%S")
        self.append_log(f"[{t}] {clean_text}")

    @Slot(str, str)
    def append_log(self, message: str, level: str = "TEXT"):
        fmt = self._formats.get(level.upper(), self._formats["TEXT"])
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.text_edit.setCurrentCharFormat(fmt)
        self.text_edit.insertPlainText(f"{message}\n")
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)


# Backwards compatibility alias
LogMessageBoxBase = OperationLogsWidget
