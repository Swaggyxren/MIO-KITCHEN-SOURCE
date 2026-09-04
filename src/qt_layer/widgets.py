import os
import time

import logging
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QHBoxLayout, QButtonGroup, QFrame, QListWidget)
from qfluentwidgets import InfoBar, InfoBarPosition, ListWidget, CheckBox, LineEdit, ComboBox, SubtitleLabel, \
    RadioButton, PushButton, BodyLabel
from qfluentwidgets import (MessageBoxBase, SwitchButton, Slider,
                            CaptionLabel)

import utils
from utils import gettype


def show_info_bar(parent, title, content, bar_type: int = 3, duration=3000):
    """bar_type: 1=error 2=warning 3=info"""
    """显示提示条，根据配置决定是否显示"""
    if True:
        if bar_type == 1:
            InfoBar.error(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=duration,
                parent=parent
            )
        elif bar_type == 2:
            InfoBar.warning(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=duration,
                parent=parent
            )
        else:
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=duration,
                parent=parent
            )

class NewProjectDialog(MessageBoxBase):
    """自定义对话框，用于创建或重命名项目"""
    def __init__(self, title, existing_projects, initial_text="", parent=None):
        super().__init__(parent)
        self.existing_projects = existing_projects

        self.titleLabel = SubtitleLabel(title, self)
        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setPlaceholderText('Enter project name')
        self.nameLineEdit.setClearButtonEnabled(True)
        self.nameLineEdit.setText(initial_text)

        self.errorLabel = CaptionLabel(text="Project name invalid or already exists")
        self.errorLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameLineEdit)
        self.viewLayout.addWidget(self.errorLabel)
        self.errorLabel.hide()

        self.widget.setMinimumWidth(350)
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.cancelButton)

        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.reject)
        self.nameLineEdit.returnPressed.connect(self.yesButton.click)

    def __onYesButtonClicked(self):
        if self.validate():
            self.accept()
        else:
            self.yesButton.setEnabled(True)

    def validate(self):
        project_name = self.nameLineEdit.text().strip()
        if not project_name:
            self.errorLabel.setText("Project name cannot be empty")
            self.errorLabel.show()
            return False

        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in project_name for char in invalid_chars):
            self.errorLabel.setText("Name contains invalid characters")
            self.errorLabel.show()
            return False

        if project_name in self.existing_projects:
            self.errorLabel.setText("Project name already exists")
            self.errorLabel.show()
            return False

        self.errorLabel.hide()
        return True

class InputDialog(MessageBoxBase):
    """Dialog for creating or renaming items"""
    def __init__(self, title, initial_text="", parent=None):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel(title, self)
        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setPlaceholderText('Input')
        self.nameLineEdit.setClearButtonEnabled(True)
        self.nameLineEdit.setText(initial_text)

        self.errorLabel = CaptionLabel(text="Invalid")
        self.errorLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameLineEdit)
        self.viewLayout.addWidget(self.errorLabel)
        self.errorLabel.hide()

        self.widget.setMinimumWidth(350)
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.cancelButton)

        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.reject)
        self.nameLineEdit.returnPressed.connect(self.yesButton.click)

    def __onYesButtonClicked(self):
        if self.validate():
            self.accept()
        else:
            self.yesButton.setEnabled(True)

    def validate(self):
        project_name = self.nameLineEdit.text().strip()
        if not project_name:
            self.errorLabel.setText("Cannot be empty")
            self.errorLabel.show()
            return False

        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in project_name for char in invalid_chars):
            self.errorLabel.setText("Contains invalid characters")
            self.errorLabel.show()
            return False

        self.errorLabel.hide()
        return True
#         if dialog.exec():
#             project_name = dialog.nameLineEdit.text().strip()
#             self.create_project(project_name)


from PySide6.QtCore import Slot
from PySide6.QtWidgets import QListWidgetItem
from qfluentwidgets import (
    MessageBoxBase,
)


class ConvertImageMessageBox(MessageBoxBase):

    def __init__(self, path: str, parent=None):
        """
        :param items: 传入要在列表中显示的文件名列表，例如 ["odm.img", "vendor.img", "system.img"]
        """
        super().__init__(parent)
        self.path = path  # 保存原始完整列表，用于搜索过滤

        # 1. 设置标准对话框标题与底层按钮文本
        self.titleLabel = SubtitleLabel("Convert image", self)
        self.yesButton.setText("OK")
        self.cancelButton.setText("Cancel")

        # 2. 创建源与目标格式下拉框
        self.src_combo = ComboBox(self)
        self.src_combo.addItems(["raw", "sparse", "dat", "br", "xz"])
        self.src_combo.currentTextChanged.connect(self.refresh_list)
        self.src_combo.setFixedWidth(160)

        self.arrow_label = SubtitleLabel(">>>>>>", self)
        self.arrow_label.setStyleSheet("color: gray;")

        self.dst_combo = ComboBox(self)
        self.dst_combo.addItems(["raw", "sparse", "dat", "br", "xz"])
        self.dst_combo.setFixedWidth(160)

        # 3. 创建核心文件多选列表 (使用 Fluent 风格的 ListWidget)
        self.list_widget = ListWidget(self)
        self.list_widget.setMinimumHeight(120)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1e;
                border: 1px solid #2d2d38;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
                color: #e4e4e7;
            }
            QListWidget::item:selected {
                background: transparent;
                color: #e4e4e7;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)

        # 4. 创建底部控制部件：全选复选框 & 搜索输入框
        self.select_all_checkbox = CheckBox("Select all", self)
        self.search_input = LineEdit(self)
        self.search_input.setPlaceholderText("search...")
        self.search_input.setClearButtonEnabled(True)

        # 5. 构建布局结构
        # 顶部的转换格式选择水平布局
        self.combo_layout = QHBoxLayout()
        self.combo_layout.setSpacing(15)
        self.combo_layout.addWidget(self.src_combo)
        self.combo_layout.addWidget(self.arrow_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.combo_layout.addWidget(self.dst_combo)

        # 底部的全选与搜索框水平布局
        self.bottom_control_layout = QHBoxLayout()
        self.bottom_control_layout.setSpacing(10)
        self.bottom_control_layout.addWidget(self.select_all_checkbox)
        self.bottom_control_layout.addWidget(self.search_input, 1)

        # 将所有部件顺次组合到 MessageBoxBase 的主视图容器中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(self.combo_layout)
        self.viewLayout.addWidget(self.list_widget)  # 插入中间的多选列表
        self.viewLayout.addLayout(self.bottom_control_layout)

        # 设置对话框的整体宽度
        self.widget.setMinimumWidth(450)

        # 6. 绑定内部交互信号槽
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        self.refresh_list()

    def refile(self, f):
        for i in os.listdir(self.path):
            if i.endswith(f) and os.path.isfile(f'{self.path}/{i}'):
                yield i
    def refresh_list(self):
        work = self.path
        file_list = []
        if self.src_combo.currentText() == "br":
            for i in self.refile(".new.dat.br"):
                file_list.append(i)
        elif self.src_combo.currentText() == 'xz':
            for i in self.refile(".new.dat.xz"):
                file_list.append(i)
        elif self.src_combo.currentText() == 'dat':
            for i in self.refile(".new.dat"):
                file_list.append(i)
        elif self.src_combo.currentText() == 'sparse':
            for i in os.listdir(work):
                if os.path.isfile(f'{work}/{i}') and gettype(f'{work}/{i}') == 'sparse':
                    file_list.append(i)
        elif self.src_combo.currentText() == 'raw':
            for i in os.listdir(work):
                if os.path.isfile(f'{work}/{i}'):
                    if gettype(f'{work}/{i}') in ['ext', 'erofs', 'super', 'f2fs']:
                        file_list.append(i)
        self._populate_list(file_list)
    def _populate_list(self, items_to_show: list[str]):
        """根据传入的列表渲染 QListWidget 项（带复选框）"""
        self.list_widget.blockSignals(True)  # 渲染时暂时阻塞信号，防止触发频繁回调
        self.list_widget.clear()
        for item_text in items_to_show:
            item = QListWidgetItem(item_text)
            # 设置该项为可勾选状态，并默认不勾选 (移除选择高亮)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

    @Slot(int)
    def _on_select_all_changed(self, state: int):
        """处理点击 'Select all' 时的全选/全不选逻辑"""
        self.list_widget.blockSignals(True)
        # 根据 Select all 的状态决定列表中每一项的勾选状态
        check_state = Qt.CheckState.Checked if state == 2 else Qt.CheckState.Unchecked
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # 只有在列表当前可见的情况下才受全选影响
            if not self.list_widget.isRowHidden(i):
                item.setCheckState(check_state)
        self.list_widget.blockSignals(False)

    @Slot(QListWidgetItem)
    def _on_item_changed(self, item: QListWidgetItem):
        """如果用户手动取消勾选了某一项，自动让底部的 'Select all' 变成未完全勾选状态"""
        self.select_all_checkbox.blockSignals(True)
        total_visible = 0
        total_checked = 0
        for i in range(self.list_widget.count()):
            if not self.list_widget.isRowHidden(i):
                total_visible += 1
                if self.list_widget.item(i).checkState() == Qt.CheckState.Checked:
                    total_checked += 1

        # 联动更新全选框的状态
        if total_checked == total_visible and total_visible > 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        elif total_checked == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        else:
            # 部分勾选状态 (PartiallyChecked)
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    @Slot(str)
    def _on_search_text_changed(self, text: str):
        """处理搜索框文本变化，实时过滤隐藏不匹配的项"""
        search_text = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # 模糊匹配：如果文件名包含输入字符则显示，否则隐藏
            is_match = search_text in item.text().lower()
            self.list_widget.setRowHidden(i, not is_match)

    def get_result(self):
        """获取用户当前在对话框中选择和输入的最终数据"""
        selected_files = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_files.append(item.text())

        return self.src_combo.currentText(),self.dst_combo.currentText(),selected_files



class SettingsCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self.setStyleSheet("""
            QFrame#settingsCard {
                background-color: #1c1c22;
                border: 1px solid #2d2d38;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(16, 12, 16, 14)
        self.card_layout.setSpacing(10)

        header = QLabel(title.upper(), self)
        header.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
        self.card_layout.addWidget(header)


class PackSettingsDialog(MessageBoxBase):
    """
    Advanced Partition Packing Settings Dialog:
    Structured into organized Fluent cards for Filesystem Options and Output Options.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Dialog header title & description
        self.titleLabel = SubtitleLabel("Partition Packing Settings", self)
        self.titleLabel.setStyleSheet("color: #f4f4f5; font-size: 17px; font-weight: 600;")
        self.subtitleLabel = CaptionLabel("Configure filesystem formats, compression parameters, and packaging options.", self)
        self.subtitleLabel.setStyleSheet("color: #a1a1aa; font-size: 12px; margin-bottom: 4px;")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.subtitleLabel)

        # Custom content container
        self.content_widget = QWidget(self)
        self.initCustomUI()
        self.viewLayout.addWidget(self.content_widget)

        # Action buttons
        self.yesButton.setText("Pack")
        self.cancelButton.setText("Cancel")

        self.widget.setMinimumWidth(640)

    def _field_lbl(self, text, parent):
        lbl = QLabel(text, parent)
        lbl.setStyleSheet("color: #e4e4e7; font-size: 13px; font-weight: 500; border: none;")
        return lbl

    def _sub_lbl(self, text, parent):
        lbl = QLabel(text, parent)
        lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; border: none;")
        return lbl

    def _switch_lbl(self, text, parent):
        lbl = QLabel(text, parent)
        lbl.setStyleSheet("color: #d4d4d8; font-size: 13px; border: none;")
        return lbl

    def _divider(self, parent):
        div = QFrame(parent)
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #272730; background-color: #272730; max-height: 1px; border: none; margin: 4px 0;")
        return div

    def initCustomUI(self):
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(0, 0, 0, 4)
        main_layout.setSpacing(12)

        # =========================================================================
        # 📂 CARD 1: Filesystem Configuration (EXT4, EROFS, F2FS)
        # =========================================================================
        fs_card = SettingsCard("Filesystem Configuration", self.content_widget)

        # --- EXT4 Section ---
        fs_card.card_layout.addWidget(self._sub_lbl("EXT4 Options", fs_card))
        ext4_row = QHBoxLayout()
        ext4_row.setSpacing(16)

        # Pack Method
        pm_col = QVBoxLayout()
        pm_col.setSpacing(4)
        pm_col.addWidget(self._field_lbl("Pack Method", fs_card))
        self.pack_method_combo = ComboBox(fs_card)
        self.pack_method_combo.addItems(["make_ext4fs", "mke2fs+e2fsdroid"])
        self.pack_method_combo.setFixedHeight(32)
        pm_col.addWidget(self.pack_method_combo)
        ext4_row.addLayout(pm_col, 1)

        # Size Handling
        sh_col = QVBoxLayout()
        sh_col.setSpacing(4)
        sh_col.addWidget(self._field_lbl("Size Handling", fs_card))
        self.size_handle_combo = ComboBox(fs_card)
        self.size_handle_combo.addItems(["Auto Detect", "Manual Fixed"])
        self.size_handle_combo.setFixedHeight(32)
        sh_col.addWidget(self.size_handle_combo)
        ext4_row.addLayout(sh_col, 1)

        fs_card.card_layout.addLayout(ext4_row)
        fs_card.card_layout.addWidget(self._divider(fs_card))

        # --- EROFS Section ---
        fs_card.card_layout.addWidget(self._sub_lbl("EROFS Options", fs_card))
        erofs_row1 = QHBoxLayout()
        erofs_row1.setSpacing(16)

        # Algo
        algo_col = QVBoxLayout()
        algo_col.setSpacing(4)
        algo_col.addWidget(self._field_lbl("Compression Algorithm", fs_card))
        self.compress_algo_combo = ComboBox(fs_card)
        self.compress_algo_combo.addItems(["lz4", "lz4hc", "lzma", "deflate", "zstd"])
        self.compress_algo_combo.setCurrentText("lz4hc")
        self.compress_algo_combo.setFixedHeight(32)
        algo_col.addWidget(self.compress_algo_combo)
        erofs_row1.addLayout(algo_col, 1)

        # Old Kernel Switch
        old_kernel_col = QVBoxLayout()
        old_kernel_col.setSpacing(4)
        old_kernel_col.addWidget(self._field_lbl("Legacy Compatibility", fs_card))
        sw_kernel_row = QHBoxLayout()
        sw_kernel_row.setSpacing(8)
        self.support_old_kernel_switch = SwitchButton(fs_card)
        self.support_old_kernel_switch.setOffText("")
        self.support_old_kernel_switch.setOnText("")
        self.support_old_kernel_label = self._switch_lbl("Support Old Kernel (< 5.4)", fs_card)
        sw_kernel_row.addWidget(self.support_old_kernel_switch)
        sw_kernel_row.addWidget(self.support_old_kernel_label)
        sw_kernel_row.addStretch(1)
        old_kernel_col.addLayout(sw_kernel_row)
        erofs_row1.addLayout(old_kernel_col, 1)
        fs_card.card_layout.addLayout(erofs_row1)

        # Slider row
        erofs_slider_row = QHBoxLayout()
        erofs_slider_row.setSpacing(12)
        self.erofs_level_label = QLabel("EROFS Level: 8", fs_card)
        self.erofs_level_label.setStyleSheet("color: #e4e4e7; font-size: 13px; font-weight: 500; min-width: 105px;")
        self.erofs_slider = Slider(Qt.Orientation.Horizontal, fs_card)
        self.erofs_slider.setRange(0, 20)
        self.erofs_slider.setValue(8)
        self.erofs_slider.valueChanged.connect(lambda v: self.erofs_level_label.setText(f"EROFS Level: {v}"))
        erofs_slider_row.addWidget(self.erofs_level_label)
        erofs_slider_row.addWidget(self.erofs_slider, 1)
        fs_card.card_layout.addLayout(erofs_slider_row)

        fs_card.card_layout.addWidget(self._divider(fs_card))

        # --- F2FS Section ---
        fs_card.card_layout.addWidget(self._sub_lbl("F2FS Options", fs_card))
        f2fs_row = QHBoxLayout()
        f2fs_row.setSpacing(24)

        f2fs_ro_box = QHBoxLayout()
        f2fs_ro_box.setSpacing(8)
        self.f2fs_readonly_switch = SwitchButton(fs_card)
        self.f2fs_readonly_switch.setOnText("")
        self.f2fs_readonly_switch.setOffText("")
        self.f2fs_readonly_lbl = self._switch_lbl("Read-only Filesystem", fs_card)
        f2fs_ro_box.addWidget(self.f2fs_readonly_switch)
        f2fs_ro_box.addWidget(self.f2fs_readonly_lbl)
        f2fs_row.addLayout(f2fs_ro_box)

        f2fs_comp_box = QHBoxLayout()
        f2fs_comp_box.setSpacing(8)
        self.f2fs_compress_switch = SwitchButton(fs_card)
        self.f2fs_compress_switch.setOnText("")
        self.f2fs_compress_switch.setOffText("")
        self.f2fs_compress_lbl = self._switch_lbl("Filesystem Compression", fs_card)
        f2fs_comp_box.addWidget(self.f2fs_compress_switch)
        f2fs_comp_box.addWidget(self.f2fs_compress_lbl)
        f2fs_row.addLayout(f2fs_comp_box)
        f2fs_row.addStretch(1)

        fs_card.card_layout.addLayout(f2fs_row)
        main_layout.addWidget(fs_card)

        # =========================================================================
        # ⚙️ CARD 2: Output & Build Options
        # =========================================================================
        build_card = SettingsCard("Packaging & Output Options", self.content_widget)

        # Format & FS Conversion Row
        out_row = QHBoxLayout()
        out_row.setSpacing(16)

        format_col = QVBoxLayout()
        format_col.setSpacing(4)
        format_col.addWidget(self._field_lbl("Output Image Format", build_card))
        self.format_combo = ComboBox(build_card)
        self.format_combo.addItems(["raw", "sparse"])
        self.format_combo.setFixedHeight(32)
        format_col.addWidget(self.format_combo)
        out_row.addLayout(format_col, 1)

        conv_col = QVBoxLayout()
        conv_col.setSpacing(4)
        conv_col.addWidget(self._field_lbl("Format Conversion", build_card))
        conv_sw_row = QHBoxLayout()
        conv_sw_row.setSpacing(8)
        self.sw_convert = SwitchButton(build_card)
        self.sw_convert.setOffText('')
        self.sw_convert.setOnText('')
        self.lbl_convert = self._switch_lbl("Enable FS Conversion", build_card)
        conv_sw_row.addWidget(self.sw_convert)
        conv_sw_row.addWidget(self.lbl_convert)
        conv_sw_row.addStretch(1)
        conv_col.addLayout(conv_sw_row)
        out_row.addLayout(conv_col, 1)
        build_card.card_layout.addLayout(out_row)

        # Conversion sub-row (collapsible)
        self.conv_detail_widget = QWidget(build_card)
        conv_detail_layout = QHBoxLayout(self.conv_detail_widget)
        conv_detail_layout.setContentsMargins(8, 4, 8, 4)
        conv_detail_layout.setSpacing(10)
        self.conv_detail_widget.setStyleSheet("""
            QWidget {
                background-color: #141418;
                border: 1px solid #2d2d38;
                border-radius: 6px;
            }
        """)

        lbl_src = QLabel("Source:", self.conv_detail_widget)
        lbl_src.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        self.src_fs_combo = ComboBox(self.conv_detail_widget)
        self.src_fs_combo.addItems(["ext", "f2fs", "erofs"])
        self.src_fs_combo.setFixedHeight(30)

        lbl_arrow = QLabel("➔", self.conv_detail_widget)
        lbl_arrow.setStyleSheet("color: #38bdf8; font-size: 14px; font-weight: bold;")

        lbl_dst = QLabel("Target:", self.conv_detail_widget)
        lbl_dst.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        self.dest_fs_combo = ComboBox(self.conv_detail_widget)
        self.dest_fs_combo.addItems(["ext", "f2fs", "erofs"])
        self.dest_fs_combo.setFixedHeight(30)

        conv_detail_layout.addWidget(lbl_src)
        conv_detail_layout.addWidget(self.src_fs_combo, 1)
        conv_detail_layout.addWidget(lbl_arrow)
        conv_detail_layout.addWidget(lbl_dst)
        conv_detail_layout.addWidget(self.dest_fs_combo, 1)

        self.conv_detail_widget.hide()
        self.sw_convert.checkedChanged.connect(self._on_convert_toggled)
        build_card.card_layout.addWidget(self.conv_detail_widget)

        # Brotli Level Slider
        brotli_row = QHBoxLayout()
        brotli_row.setSpacing(12)
        self.brotli_lbl = QLabel("Brotli Level: 0", build_card)
        self.brotli_lbl.setStyleSheet("color: #e4e4e7; font-size: 13px; font-weight: 500; min-width: 105px;")
        self.brotli_slider = Slider(Qt.Orientation.Horizontal, build_card)
        self.brotli_slider.setRange(0, 11)
        self.brotli_slider.setValue(0)
        self.brotli_slider.valueChanged.connect(lambda v: self.brotli_lbl.setText(f"Brotli Level: {v}"))
        brotli_row.addWidget(self.brotli_lbl)
        brotli_row.addWidget(self.brotli_slider, 1)
        build_card.card_layout.addLayout(brotli_row)

        # UTC Timestamp row
        utc_row = QHBoxLayout()
        utc_row.setSpacing(10)
        self.utc_lbl = self._field_lbl("Build Timestamp (UTC):", build_card)
        self.utc_lbl.setMinimumWidth(150)
        self.utc_input = QLineEdit(str(int(time.time())), build_card)
        self.utc_input.setStyleSheet("""
            QLineEdit {
                background-color: #141418;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                color: #38bdf8;
                padding: 4px 8px;
                font-family: monospace;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        self.btn_now = PushButton("Current Time", build_card)
        self.btn_now.setFixedHeight(28)
        self.btn_now.clicked.connect(lambda: self.utc_input.setText(str(int(time.time()))))

        utc_row.addWidget(self.utc_lbl)
        utc_row.addWidget(self.utc_input, 1)
        utc_row.addWidget(self.btn_now)
        build_card.card_layout.addLayout(utc_row)

        build_card.card_layout.addWidget(self._divider(build_card))

        # Bottom Safety & Flags Row
        flags_row = QHBoxLayout()
        flags_row.setSpacing(24)

        vb_box = QHBoxLayout()
        vb_box.setSpacing(8)
        self.sw_vbmeta = SwitchButton(build_card)
        self.sw_vbmeta.setOffText("")
        self.sw_vbmeta.setOnText("")
        self.lbl_vbmeta = self._switch_lbl("Patch Vbmeta (AVB Flag)", build_card)
        vb_box.addWidget(self.sw_vbmeta)
        vb_box.addWidget(self.lbl_vbmeta)
        flags_row.addLayout(vb_box)

        del_box = QHBoxLayout()
        del_box.setSpacing(8)
        self.sw_delete = SwitchButton(build_card)
        self.sw_delete.setOffText("")
        self.sw_delete.setOnText("")
        self.lbl_delete = self._switch_lbl("Delete Source Files After Packing", build_card)
        del_box.addWidget(self.sw_delete)
        del_box.addWidget(self.lbl_delete)
        flags_row.addLayout(del_box)
        flags_row.addStretch(1)

        build_card.card_layout.addLayout(flags_row)
        main_layout.addWidget(build_card)

    def _on_convert_toggled(self, is_checked: bool):
        self.conv_detail_widget.setVisible(is_checked)
        self.content_widget.adjustSize()
        self.widget.adjustSize()


OPLUS_PARTITIONS = [
    "my_product", "my_region", "my_heytap", "my_stock", "my_carrier",
    "my_preload", "my_engineering", "my_bigball", "my_manifest", "my_company"
]


class PackSuperMessageBox(MessageBoxBase):
    def __init__(self, work_path, parent=None):
        super().__init__(parent)
        self.work = work_path
        self.selected = []
        self._block_device_name = 'super'

        # Window styling configuration
        self.widget.setMinimumWidth(450)

        # 1. Main Header Title
        self.titleLabel = SubtitleLabel("Pack Super", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 2. Partition Type Section
        self.viewLayout.addWidget(SubtitleLabel("Partition Type", self))
        lf1_layout = QHBoxLayout()
        self.type_group = QButtonGroup(self)
        radios = [("A-only", 1), ("Virtual-ab", 2), ("A/B", 3)]
        for text, value in radios:
            rb = RadioButton(text, self)
            self.type_group.addButton(rb, value)
            lf1_layout.addWidget(rb)
        if self.type_group.button(1):
            self.type_group.button(1).setChecked(True)
        self.viewLayout.addLayout(lf1_layout)

        # 3. Attributes Section
        self.viewLayout.addWidget(SubtitleLabel("Attributes", self))
        lf1_r_layout = QHBoxLayout()
        self.attrib_group = QButtonGroup(self)
        self.rb_readonly = RadioButton("Readonly", self)
        self.rb_none = RadioButton("None", self)
        self.attrib_group.addButton(self.rb_readonly, 0)
        self.attrib_group.addButton(self.rb_none, 1)
        self.rb_readonly.setChecked(True)
        lf1_r_layout.addWidget(self.rb_readonly)
        lf1_r_layout.addWidget(self.rb_none)
        self.viewLayout.addLayout(lf1_r_layout)

        # 4. Settings Section
        self.viewLayout.addWidget(SubtitleLabel("Settings", self))
        lf2_layout = QHBoxLayout()

        lf2_layout.addWidget(SubtitleLabel("Group Name", self))
        self.show_group_name = ComboBox(self)
        self.show_group_name.addItems(["qti_dynamic_partitions", "oplus_dynamic_partitions", "main", "mot_dp_group"])
        self.show_group_name.setCurrentIndex(0)
        lf2_layout.addWidget(self.show_group_name)

        lf2_layout.addWidget(SubtitleLabel("Super Size", self))
        self.super_size_edit = LineEdit(self)
        self.super_size_edit.setText("9126805504")
        self.super_size_edit.textChanged.connect(self.validate_digits)
        lf2_layout.addWidget(self.super_size_edit)
        self.viewLayout.addLayout(lf2_layout)

        # 5. Pack Partitions Section
        self.viewLayout.addWidget(SubtitleLabel("Pack Partitions", self))
        self.tl = ListWidget(self)
        self.tl.setMinimumHeight(180)
        self.tl.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.tl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tl.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1e;
                border: 1px solid #2d2d38;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
                color: #e4e4e7;
            }
            QListWidget::item:selected {
                background: transparent;
                color: #e4e4e7;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.viewLayout.addWidget(self.tl)

        # 6. Checkboxes & Action Layout Configurations
        self.switch_sparse = SwitchButton(self)
        self.switch_sparse.setOffText("Sparse Compression")
        self.switch_sparse.setOnText("Sparse Compression")
        self.viewLayout.addWidget(self.switch_sparse)

        t_frame_layout = QHBoxLayout()
        self.switch_delete = SwitchButton(self)
        self.switch_delete.setOffText("Delete Source Files")
        self.switch_delete.setOnText("Delete Source Files")
        t_frame_layout.addWidget(self.switch_delete)

        self.btn_refresh = PushButton("Refresh", self)
        self.btn_refresh.clicked.connect(self.refresh)
        t_frame_layout.addWidget(self.btn_refresh)

        self.g_b = PushButton("Generate List", self)
        self.g_b.clicked.connect(self.generate)
        t_frame_layout.addWidget(self.g_b)
        self.viewLayout.addLayout(t_frame_layout)

        # 7. Bottom Accept/Cancel Bar configuration setups
        self.yesButton.setText("Pack")
        self.cancelButton.setText("Cancel")
        self.read_list()
        self.refresh()

    def validate_digits(self, text):
        """Sanitizes line edit inputs to keep digit formatting clean."""
        if not text.isdigit() and text != "":
            clean_text = "".join(filter(str.isdigit, text))
            self.super_size_edit.setText(clean_text)

    def get_selected_items(self):
        """Extracts current checkable choices context keys from list layout directly."""
        checked_names = []
        for i in range(self.tl.count()):
            item = self.tl.item(i)
            if item.checkState() == Qt.Checked:
                checked_names.append(item.data(Qt.UserRole))
        return checked_names

    def verify_size(self):
        selected_lbs = self.get_selected_items()
        size = sum(
            [os.path.getsize(f"{self.work}/{i}.img") for i in selected_lbs if os.path.exists(f"{self.work}/{i}.img")])

        try:
            current_size = int(self.super_size_edit.text() or "0")
        except ValueError:
            current_size = 0

        if size > current_size:
            diff_size = size
            for i in range(20):
                if not i:
                    continue
                i -= 0.25
                t = (1024 ** 3) * i - size
                if t < 0:
                    continue
                if t < diff_size:
                    diff_size = t
                else:
                    size = i * (1024 ** 3)
                    break
            self.super_size_edit.setText(str(int(size)))
            return False
        return True

    def generate(self):
        self.g_b.setText("Generating...")
        self.g_b.setEnabled(False)
        self.g_b.repaint()

        try:
            size_val = int(self.super_size_edit.text() or "0")
        except ValueError:
            size_val = 0

        utils.generate_dynamic_list(
            group_name=self.show_group_name.currentText(),
            size=size_val,
            super_type=self.type_group.checkedId(),
            part_list=self.get_selected_items(),
            work=self.work
        )
        self.g_b.setText("Completed")
        QTimer.singleShot(1000, self._reset_generate_button)

    def _reset_generate_button(self):
        try:
            self.g_b.setText("Generate List")
            self.g_b.setEnabled(True)
        except Exception:
            logging.exception('Bugs')

    def refresh(self):
        self.tl.clear()
        if not os.path.exists(self.work):
            return

        has_oplus_parts = False
        for file_name in os.listdir(self.work):
            if file_name.endswith(".img"):
                img_path = os.path.join(self.work, file_name)
                name = file_name[:-4]
                if name.startswith("my_") or name in OPLUS_PARTITIONS:
                    has_oplus_parts = True
                is_checked = name in self.selected
                item_text = ""

                if utils.is_empty_img(img_path):
                    item_text = f"{name} [empty]"
                else:
                    file_type = gettype(img_path)
                    if file_type in ["ext", "erofs", 'f2fs', 'sparse']:
                        item_text = f"{name} [{file_type}]"

                if item_text:
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, name)
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
                    self.tl.addItem(item)

        if has_oplus_parts and self.show_group_name.currentText() == "qti_dynamic_partitions":
            oplus_idx = self.show_group_name.findText("oplus_dynamic_partitions")
            if oplus_idx >= 0:
                self.show_group_name.setCurrentIndex(oplus_idx)

        self.verify_size()

    def read_list(self):
        # Read parts_config
        parts_info = f"{self.work}/config/parts_info"
        if os.path.exists(parts_info):
            try:
                raw_data = utils.JsonEdit(parts_info).read()
                data = raw_data.get('super_info') if isinstance(raw_data, dict) else None
            except Exception:
                logging.exception('PackSuper:read_parts_info')
                data = None

            if isinstance(data, dict):
                # get block device name
                for i in data.get('block_devices', []):
                    self._block_device_name = i.get('name', 'super')
                    if isinstance(i.get('size'), int):
                        self.super_size_edit.setText(str(i.get('size')))

                for i in data.get('group_table', []):
                    name = i.get('name')
                    if isinstance(name, str) and name != 'default':
                        index = self.show_group_name.findText(name)
                        if index >= 0:
                            self.show_group_name.setCurrentIndex(index)
                        else:
                            self.show_group_name.addItem(name)
                            self.show_group_name.setCurrentText(name)

                selected = []
                for i in data.get('partition_table', []):
                    name = i.get('name')
                    if isinstance(name, str) and name not in selected:
                        selected.append(name)
                self.selected = selected

        # Read dynamic_partitions_op_list
        list_file = f"{self.work}/dynamic_partitions_op_list"
        if os.path.exists(list_file):
            try:
                data = utils.dynamic_list_reader(list_file)
            except Exception:
                logging.exception('Bugs')
                return

            if not isinstance(data, dict) or not data:
                return

            keys = list(data.keys())

            if len(keys) > 1:
                fir = keys[0]
                sec = keys[1]
                if fir[:-2] == sec[:-2]:
                    g_name = fir[:-2]
                    index = self.show_group_name.findText(g_name)
                    if index >= 0:
                        self.show_group_name.setCurrentIndex(index)
                    else:
                        self.show_group_name.addItem(g_name)
                        self.show_group_name.setCurrentText(g_name)

                    if self.type_group.button(2):
                        self.type_group.button(2).setChecked(True)

                    self.super_size_edit.setText(str(int(data[fir]['size'])))
                    self.selected = data[fir].get('parts', [])

                    selected_copy = self.selected.copy()
                    for i in self.selected:
                        name = i[:-2] if i.endswith('_a') or i.endswith('_b') else i
                        if name not in selected_copy:
                            selected_copy.append(name)
                    self.selected = selected_copy

            elif len(keys) == 1:
                group_name = keys[0]
                index = self.show_group_name.findText(group_name)
                if index >= 0:
                    self.show_group_name.setCurrentIndex(index)
                else:
                    self.show_group_name.addItem(group_name)
                    self.show_group_name.setCurrentText(group_name)

                self.super_size_edit.setText(str(int(data[group_name]['size'])))
                self.selected = data[group_name].get('parts', [])

                if self.type_group.button(1):
                    self.type_group.button(1).setChecked(True)


class RepackZipMessageBox(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pack ZIP")
        self.widget.setMinimumWidth(550)

        # 1. Title
        self.titleLabel = SubtitleLabel("Repack ZIP?", self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.viewLayout.addWidget(self.titleLabel)

        # 2. CheckBox & Content Text Layout
        self.checkbox_layout = QHBoxLayout()
        self.checkbox = CheckBox(self)

        msg_text = (
            "Pack Hybrid Rom?"
        )
        self.contentLabel = BodyLabel(msg_text, self)
        self.contentLabel.setWordWrap(True)

        self.checkbox_layout.addWidget(self.checkbox, 0, Qt.AlignTop)
        self.checkbox_layout.addWidget(self.contentLabel, 1)
        self.viewLayout.addLayout(self.checkbox_layout)

        # 3. Dynamic Device Code Input LineEdit
        self.device_code_edit = LineEdit(self)
        self.device_code_edit.setPlaceholderText("Enter device code")
        self.device_code_edit.setClearButtonEnabled(True)
        self.device_code_edit.hide()  # Hidden by default
        self.viewLayout.addWidget(self.device_code_edit)

        # Connect toggle action to state visibility switch
        self.checkbox.stateChanged.connect(self.toggle_input_visibility)

        # 4. Standard action button text overrides
        self.yesButton.setText("OK")
        self.cancelButton.setText("Cancel")

    def toggle_input_visibility(self, state):
        """Hides or reveals the LineEdit depending on the checkbox check state."""
        is_checked = (state == Qt.Checked or state == 2)  # Handles PySide6 integer/enum variants
        self.device_code_edit.setVisible(is_checked)

        # Force the Fluent MessageBox to smoothly recalculate layout sizing constraints
        self.widget.adjustSize()

    def is_add_tools_checked(self) -> bool:
        """Returns True if the check box tool integration option is selected."""
        return self.checkbox.isChecked()

    def get_device_code(self) -> str:
        """Returns the trimmed input text string from the device code line entry."""
        return self.device_code_edit.text().strip()


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)

    def enterEvent(self, event):
        """Show hand cursor when entering widget"""
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reset cursor when leaving widget"""
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)