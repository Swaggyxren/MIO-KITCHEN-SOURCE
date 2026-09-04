import datetime
import os
import random

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QColor, QCursor
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QFrame, QLabel,
                             QGridLayout, QPushButton)
from qfluentwidgets import (ScrollArea, TitleLabel, SubtitleLabel, CaptionLabel,
                            BodyLabel, PushButton, FluentIcon as FIF, IconWidget,
                            setThemeColor)

from src.qt_layer.widgets import ClickableLabel
from qt_layer.settings import cfg


class QuickActionCard(QFrame):
    """Interactive launchpad card for quick actions on Home page"""
    clicked = Signal()

    def __init__(self, icon, title: str, subtitle: str, color_hex: str = "#0078d4", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QuickActionCard {{
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }}
            QuickActionCard:hover {{
                background-color: #242424;
                border: 1px solid {color_hex};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Icon wrapper
        icon_box = QFrame(self)
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet(f"""
            QFrame {{
                background-color: {color_hex}22;
                border-radius: 6px;
                border: none;
            }}
        """)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_widget = IconWidget(icon, icon_box)
        icon_widget.setFixedSize(18, 18)
        icon_layout.addWidget(icon_widget, 0, Qt.AlignCenter)
        layout.addWidget(icon_box)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_lbl = QLabel(title, self)
        title_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        sub_lbl = QLabel(subtitle, self)
        sub_lbl.setStyleSheet("color: #777777; font-size: 11px; border: none; background: transparent;")
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(sub_lbl)
        layout.addLayout(text_layout)
        layout.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class HomePage(QWidget):
    quick_open_project = Signal()
    quick_new_project = Signal()
    quick_unpack_file = Signal()
    quick_manage_plugins = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomePage")
        setThemeColor('#0078D4')
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable container for perfect responsive display
        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("ScrollArea { border: none; background-color: #202020; }")
        main_layout.addWidget(scroll_area)

        content = QWidget()
        content.setStyleSheet("background-color: #202020; color: #FFFFFF;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 28, 36, 32)
        layout.setSpacing(20)
        scroll_area.setWidget(content)

        # 1. Top Header Banner
        header_box = QWidget()
        header_layout = QVBoxLayout(header_box)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(4)

        title = QLabel("Welcome to MIO-KITCHEN")
        title.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 700; border: none; background: transparent;")
        subtitle = QLabel("High-performance Android ROM extraction, patching & repacking studio")
        subtitle.setStyleSheet("color: #888888; font-size: 12px; border: none; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # Thin separator line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2d2d2d; border: none;")
        header_layout.addWidget(sep)
        layout.addWidget(header_box)

        # 2. Main Two-Column Body Layout
        body_layout = QHBoxLayout()
        body_layout.setSpacing(24)
        body_layout.setAlignment(Qt.AlignTop)

        # ==========================================
        # LEFT COLUMN: Interactive Companion Dock
        # ==========================================
        left_dock = QVBoxLayout()
        left_dock.setSpacing(12)

        # 2a. Dialogue Bubble
        dialog_box = QFrame()
        dialog_box.setFixedWidth(280)
        dialog_box.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }
        """)
        dialog_inner = QVBoxLayout(dialog_box)
        dialog_inner.setContentsMargins(14, 12, 14, 12)
        dialog_inner.setSpacing(6)

        header_row = QHBoxLayout()
        lbl_user = QLabel("KeMiaoJiang")
        lbl_user.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        lbl_badge = QLabel("Companion")
        lbl_badge.setStyleSheet("color: #0078d4; background-color: rgba(0, 120, 212, 0.15); font-size: 10px; font-weight: bold; border-radius: 3px; padding: 2px 5px; border: none;")
        header_row.addWidget(lbl_user)
        header_row.addStretch()
        header_row.addWidget(lbl_badge)
        dialog_inner.addLayout(header_row)

        self.lbl_msg = QLabel("Hi! What can I do for you? ✨")
        self.lbl_msg.setStyleSheet("color: #DDA0DD; font-size: 12px; font-weight: 600; line-height: 1.4; border: none; background: transparent;")
        self.lbl_msg.setWordWrap(True)
        dialog_inner.addWidget(self.lbl_msg)
        left_dock.addWidget(dialog_box)

        # 2b. Mascot Artwork Card
        mascot_card = QFrame()
        mascot_card.setFixedWidth(280)
        mascot_card.setCursor(Qt.PointingHandCursor)
        mascot_card.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 1px solid #3d3d3d;
            }
        """)
        mascot_layout = QVBoxLayout(mascot_card)
        mascot_layout.setContentsMargins(12, 16, 12, 14)
        mascot_layout.setSpacing(10)
        mascot_layout.setAlignment(Qt.AlignCenter)

        avatar_label = ClickableLabel()
        avatar_pixmap = QPixmap("bin/kemiaojiang.png")
        if not avatar_pixmap.isNull():
            avatar_label.setPixmap(avatar_pixmap.scaledToHeight(280, Qt.TransformationMode.SmoothTransformation))
        avatar_label.clicked.connect(self.cycle_dialogue)
        mascot_layout.addWidget(avatar_label, 0, Qt.AlignCenter)

        hint_lbl = QLabel("KeMiaoJiang • Updates every 30s")
        hint_lbl.setStyleSheet("color: #555555; font-size: 10px; border: none; background: transparent;")
        mascot_layout.addWidget(hint_lbl, 0, Qt.AlignCenter)
        left_dock.addWidget(mascot_card)

        # 30-second dialogue auto-cycle timer
        self.dialogue_timer = QTimer(self)
        self.dialogue_timer.setInterval(30000)
        self.dialogue_timer.timeout.connect(self.cycle_dialogue)
        self.dialogue_timer.start()

        # 2c. Credits Badge
        credits_box = QFrame()
        credits_box.setFixedWidth(280)
        credits_box.setStyleSheet("""
            QFrame {
                background-color: #181818;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
            }
        """)
        credits_layout = QHBoxLayout(credits_box)
        credits_layout.setContentsMargins(12, 8, 12, 8)
        credits_lbl = QLabel("Ambassador: KeMiaoJiang  •  Painter: HY-惠")
        credits_lbl.setStyleSheet("color: #777777; font-size: 10px; border: none; background: transparent;")
        credits_layout.addWidget(credits_lbl, 0, Qt.AlignCenter)
        left_dock.addWidget(credits_box)

        left_dock.addStretch()
        body_layout.addLayout(left_dock)

        # ==========================================
        # RIGHT COLUMN: Productivity Dashboard
        # ==========================================
        right_dash = QVBoxLayout()
        right_dash.setSpacing(16)

        # 3a. Quick Action Launchpads
        qa_header = QLabel("QUICK ACTIONS")
        qa_header.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none; background: transparent;")
        right_dash.addWidget(qa_header)

        grid = QGridLayout()
        grid.setSpacing(10)

        card1 = QuickActionCard(FIF.DOCUMENT, "Open Project Workspace", "Switch to active partition project", "#0078d4", self)
        card1.clicked.connect(self.quick_open_project)

        card2 = QuickActionCard(FIF.ADD, "New ROM Project", "Initialize clean project directory", "#107c41", self)
        card2.clicked.connect(self.quick_new_project)

        card3 = QuickActionCard(FIF.DOWNLOAD, "Unpack ROM File", "Extract zip, payload.bin, super.img", "#8764b8", self)
        card3.clicked.connect(self.quick_unpack_file)

        card4 = QuickActionCard(FIF.APPLICATION, "Manage Plugins", "Browse & run custom MPK tools", "#f7630c", self)
        card4.clicked.connect(self.quick_manage_plugins)

        grid.addWidget(card1, 0, 0)
        grid.addWidget(card2, 0, 1)
        grid.addWidget(card3, 1, 0)
        grid.addWidget(card4, 1, 1)
        right_dash.addLayout(grid)

        # 3b. Active Project Overview Card
        proj_card = QFrame()
        proj_card.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }
        """)
        proj_inner = QVBoxLayout(proj_card)
        proj_inner.setContentsMargins(16, 14, 16, 14)
        proj_inner.setSpacing(12)

        proj_top = QHBoxLayout()
        proj_title = QLabel("Active Project Overview")
        proj_title.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        proj_active_badge = QLabel("Active")
        proj_active_badge.setStyleSheet("color: #2ecc71; background-color: rgba(46, 204, 113, 0.15); font-size: 10px; font-weight: bold; border-radius: 3px; padding: 2px 6px; border: 1px solid rgba(46, 204, 113, 0.3);")
        proj_top.addWidget(proj_title)
        proj_top.addStretch()
        proj_top.addWidget(proj_active_badge)
        proj_inner.addLayout(proj_top)

        # Tiles
        tiles_layout = QHBoxLayout()
        tiles_layout.setSpacing(10)

        current_name = cfg.currentProjectName.value if cfg.currentProjectName.value else "Xiaomi_14_Global"
        tile1 = self._create_info_tile("PROJECT", current_name)
        tile2 = self._create_info_tile("PARTITIONS", "5 detected (erofs/ext4)")
        tile3 = self._create_info_tile("DEFAULT FORMAT", ".img (raw/sparse)")
        tiles_layout.addWidget(tile1)
        tiles_layout.addWidget(tile2)
        tiles_layout.addWidget(tile3)
        proj_inner.addLayout(tiles_layout)

        # Footer row with link
        footer_row = QHBoxLayout()
        loc_lbl = QLabel(f"Location: workspace/{current_name}/")
        loc_lbl.setStyleSheet("color: #777777; font-size: 11px; border: none; background: transparent;")
        manage_btn = QPushButton("Manage in Projects →")
        manage_btn.setCursor(Qt.PointingHandCursor)
        manage_btn.setStyleSheet("""
            QPushButton {
                color: #0078d4;
                font-size: 11px;
                font-weight: 600;
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        manage_btn.clicked.connect(self.quick_open_project)
        footer_row.addWidget(loc_lbl)
        footer_row.addStretch()
        footer_row.addWidget(manage_btn)
        proj_inner.addLayout(footer_row)
        right_dash.addWidget(proj_card)

        # 3c. Toolchain & Engine Readiness Card
        toolchain_card = QFrame()
        toolchain_card.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }
        """)
        tc_inner = QVBoxLayout(toolchain_card)
        tc_inner.setContentsMargins(16, 12, 16, 12)
        tc_inner.setSpacing(8)

        tc_top = QHBoxLayout()
        tc_title = QLabel("Toolchain & Engine Readiness")
        tc_title.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        tc_env = QLabel("Python 3.13 / Linux-x86_64")
        tc_env.setStyleSheet("color: #777777; font-size: 10px; font-family: monospace; border: none; background: transparent;")
        tc_top.addWidget(tc_title)
        tc_top.addStretch()
        tc_top.addWidget(tc_env)
        tc_inner.addLayout(tc_top)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(14)
        for tool in ["erofs-utils", "simg2img", "zstd", "e2fsck", "magiskboot"]:
            lbl = QLabel(f"✓  {tool}")
            lbl.setStyleSheet("color: #2ecc71; font-size: 11px; font-weight: 500; border: none; background: transparent;")
            badge_row.addWidget(lbl)
        badge_row.addStretch()
        tc_inner.addLayout(badge_row)
        right_dash.addWidget(toolchain_card)

        # 3d. Campaign & Advocacy Card
        advocacy_card = QFrame()
        advocacy_card.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }
        """)
        adv_inner = QVBoxLayout(advocacy_card)
        adv_inner.setContentsMargins(16, 12, 16, 12)
        adv_inner.setSpacing(4)

        adv_top = QHBoxLayout()
        adv_title = QLabel("Campaign & Advocacy")
        adv_title.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        adv_link = QLabel("<a href='https://keepandroidopen.org' style='color: #ff4d4d; text-decoration: underline; font-weight: 600; font-size: 11px;'>keepandroidopen.org ↗</a>")
        adv_link.setOpenExternalLinks(True)
        adv_top.addWidget(adv_title)
        adv_top.addStretch()
        adv_top.addWidget(adv_link)
        adv_inner.addLayout(adv_top)

        adv_desc = QLabel("Your phone is about to stop being yours. Protect open bootloaders, user autonomy, and independent developer rights.")
        adv_desc.setStyleSheet("color: #888888; font-size: 11px; border: none; background: transparent;")
        adv_desc.setWordWrap(True)
        adv_inner.addWidget(adv_desc)
        right_dash.addWidget(advocacy_card)

        right_dash.addStretch()
        body_layout.addLayout(right_dash, 1)

        layout.addLayout(body_layout)
        layout.addStretch()

    def _create_info_tile(self, label_text: str, val_text: str) -> QFrame:
        tile = QFrame()
        tile.setStyleSheet("""
            QFrame {
                background-color: #202020;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
            }
        """)
        l = QVBoxLayout(tile)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(2)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #777777; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        val = QLabel(val_text)
        val.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        l.addWidget(lbl)
        l.addWidget(val)
        return tile

    def cycle_dialogue(self):
        """Automatically called every 30 seconds to cycle companion message"""
        current_time = datetime.datetime.now()
        hour = current_time.hour
        time_greeting = "Good morning! ~_~" if 5 <= hour < 12 else "Good afternoon! O^O" if 12 <= hour < 18 else "Good evening! Zzz~~"

        greetings = [
            f"{time_greeting} Need me to unpack some partitions? :>",
            "Master, let's patch some fresh fs_config mappings! w^w",
            "MIO-KITCHEN is active! Let's build something awesome today! ✨",
            "Your ROM kitchen helper KeMiaoJiang is ready for commands! OwO",
            "What can I do for ya~ :)",
            "My binaries are the latest (￣▽￣)~*",
            "Need to repack super.img? Just click Quick Actions!",
            "Did you know? EROFS saves both RAM and flash storage!",
            "Ready to flash? Make sure to verify your vbmeta flags!"
        ]

        current_text = self.lbl_msg.text()
        available = [g for g in greetings if g != current_text]
        new_text = random.choice(available if available else greetings)
        self.lbl_msg.setText(new_text)

    # Alias for backwards compatibility
    react = cycle_dialogue



