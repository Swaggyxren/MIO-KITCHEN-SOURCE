import os
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QHeaderView, QTableWidgetItem, QFileDialog)
from qfluentwidgets import (TableWidget, SearchLineEdit, PushButton,
                            SubtitleLabel, CaptionLabel, MessageBox, FluentIcon as FIF,
                            IndeterminateProgressBar)

from androguard.core.apk import APK
from src.core.utils import hum_convert


class ApkScanWorker(QThread):
    apk_found = Signal(dict)
    scan_finished = Signal(int)

    def __init__(self, work_dir: str):
        super().__init__()
        self.work_dir = work_dir
        self._is_cancelled = False

    def run(self):
        apk_files = []
        if os.path.exists(self.work_dir):
            for root, _, files in os.walk(self.work_dir):
                if self._is_cancelled:
                    return
                for f in files:
                    if f.lower().endswith(".apk"):
                        apk_files.append(os.path.join(root, f))

        count = 0
        if apk_files:
            with ThreadPoolExecutor(max_workers=4) as executor:
                for info in executor.map(self._parse_apk, apk_files):
                    if self._is_cancelled:
                        return
                    if info:
                        self.apk_found.emit(info)
                        count += 1

        self.scan_finished.emit(count)

    def cancel(self):
        self._is_cancelled = True

    def _parse_apk(self, path: str):
        try:
            apk = APK(path)
            pkg = apk.get_package() or "Unknown"
            app_name = apk.get_app_name() or os.path.basename(path)
            target_sdk = str(apk.get_target_sdk_version() or "?")
            size_str = hum_convert(os.path.getsize(path))

            rel = os.path.relpath(path, self.work_dir)
            parts = rel.split(os.sep)
            partition = parts[0] if parts else "system"

            return {
                "path": path,
                "rel_path": rel,
                "filename": os.path.basename(path),
                "package": pkg,
                "app_name": app_name,
                "partition": partition,
                "size": size_str,
                "target_sdk": target_sdk
            }
        except Exception:
            rel = os.path.relpath(path, self.work_dir)
            parts = rel.split(os.sep)
            partition = parts[0] if parts else "system"
            return {
                "path": path,
                "rel_path": rel,
                "filename": os.path.basename(path),
                "package": os.path.splitext(os.path.basename(path))[0],
                "app_name": os.path.basename(path),
                "partition": partition,
                "size": hum_convert(os.path.getsize(path)),
                "target_sdk": "?"
            }


class ApkAssistantDialog(QDialog):
    def __init__(self, work_dir: str, parent=None):
        super().__init__(parent)
        self.work_dir = work_dir
        self.apk_list = []
        self._updating_checks = False

        self.setWindowTitle("APK Assistant - ROM Debloater")
        self.resize(920, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #141418;
                color: #ffffff;
            }
            QLabel {
                color: #e4e4e7;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        # Top Header
        top_layout = QHBoxLayout()
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(2)
        title = SubtitleLabel("APK Assistant", self)
        title.setStyleSheet("color: #f4f4f5; font-size: 18px; font-weight: bold;")
        desc = CaptionLabel("Inspect, search, and debloat pre-installed applications from unpacked partitions.", self)
        desc.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        header_vbox.addWidget(title)
        header_vbox.addWidget(desc)
        top_layout.addLayout(header_vbox)
        top_layout.addStretch(1)

        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Search app, package, or partition...")
        self.search_box.setFixedWidth(280)
        self.search_box.textChanged.connect(self._filter_table)
        top_layout.addWidget(self.search_box)
        layout.addLayout(top_layout)

        # Progress bar
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(3)
        layout.addWidget(self.progress_bar)

        # Status & Counter Row
        status_row = QHBoxLayout()
        self.status_lbl = QLabel("Scanning workspace for APKs...", self)
        self.status_lbl.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 500;")
        self.status_lbl.setWordWrap(True)
        status_row.addWidget(self.status_lbl, 1)
        self.count_lbl = QLabel("Total: 0 | Selected: 0", self)
        self.count_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        status_row.addWidget(self.count_lbl)
        layout.addLayout(status_row)

        # Table Widget
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Select", "App Name", "Package Name", "Partition", "Size", "Target SDK"])
        self.table.verticalHeader().hide()
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setSelectionMode(TableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 65)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 180)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 90)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 90)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 95)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table, 1)

        # Bottom Actions Bar
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_select_all = PushButton("Select All", self)
        self.btn_select_all.clicked.connect(self._select_all)
        actions_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = PushButton("Deselect All", self)
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        actions_layout.addWidget(self.btn_deselect_all)

        self.btn_import_debloat = PushButton("Import Debloat List", self, FIF.FOLDER)
        self.btn_import_debloat.clicked.connect(self._import_debloat_list)
        actions_layout.addWidget(self.btn_import_debloat)

        self.btn_export_debloat = PushButton("Export Debloat List", self, FIF.SHARE)
        self.btn_export_debloat.clicked.connect(self._export_debloat_list)
        actions_layout.addWidget(self.btn_export_debloat)

        actions_layout.addStretch(1)

        self.btn_remove = PushButton("Remove Selected", self)
        self.btn_remove.setMinimumWidth(140)
        self.btn_remove.setStyleSheet("""
            PushButton {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px solid #ef4444;
                color: #f87171;
                font-weight: 600;
            }
            PushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.btn_remove.clicked.connect(self._remove_selected)
        actions_layout.addWidget(self.btn_remove)

        self.btn_close = PushButton("Close", self)
        self.btn_close.setMinimumWidth(80)
        self.btn_close.clicked.connect(self.accept)
        actions_layout.addWidget(self.btn_close)

        layout.addLayout(actions_layout)

        # Launch background scanner worker
        self.worker = ApkScanWorker(self.work_dir)
        self.worker.apk_found.connect(self._add_apk_row)
        self.worker.scan_finished.connect(self._on_scan_finished)
        self.worker.start()

    def _add_apk_row(self, info: dict):
        self.apk_list.append(info)
        row = self.table.rowCount()
        self.table.insertRow(row)

        chk_item = QTableWidgetItem()
        chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chk_item.setCheckState(Qt.CheckState.Unchecked)
        chk_item.setData(Qt.ItemDataRole.UserRole, info)

        name_item = QTableWidgetItem(info["app_name"])
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

        pkg_item = QTableWidgetItem(info["package"])
        pkg_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

        part_item = QTableWidgetItem(info["partition"])
        part_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        part_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        size_item = QTableWidgetItem(info["size"])
        size_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        sdk_item = QTableWidgetItem(info["target_sdk"])
        sdk_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        sdk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table.setItem(row, 0, chk_item)
        self.table.setItem(row, 1, name_item)
        self.table.setItem(row, 2, pkg_item)
        self.table.setItem(row, 3, part_item)
        self.table.setItem(row, 4, size_item)
        self.table.setItem(row, 5, sdk_item)

        self._update_counter()

    def _on_scan_finished(self, count: int):
        self.progress_bar.hide()
        if count == 0:
            self.status_lbl.setText("No APK files found in current workspace. Make sure partitions are unpacked.")
            self.status_lbl.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: 500;")
        else:
            self.status_lbl.setText(f"Scan complete: {count} applications found.")
            self.status_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 500;")
        self._update_counter()

    def _filter_table(self, text: str):
        query = text.strip().lower()
        for row in range(self.table.rowCount()):
            if not query:
                self.table.setRowHidden(row, False)
                continue
            name = (self.table.item(row, 1).text() if self.table.item(row, 1) else "").lower()
            pkg = (self.table.item(row, 2).text() if self.table.item(row, 2) else "").lower()
            part = (self.table.item(row, 3).text() if self.table.item(row, 3) else "").lower()
            match = query in name or query in pkg or query in part
            self.table.setRowHidden(row, not match)

    def _select_all(self):
        self._updating_checks = True
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked)
        self._updating_checks = False
        self._update_counter()

    def _deselect_all(self):
        self._updating_checks = True
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self._updating_checks = False
        self._update_counter()

    def _on_cell_clicked(self, row, column):
        if column != 0:
            item = self.table.item(row, 0)
            if item is not None:
                new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(new_state)

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0 and not self._updating_checks:
            self._update_counter()

    def _update_counter(self):
        total = self.table.rowCount()
        selected = sum(
            1 for row in range(total)
            if self.table.item(row, 0) and self.table.item(row, 0).checkState() == Qt.CheckState.Checked
        )
        self.count_lbl.setText(f"Total: {total} | Selected: {selected}")
        self.btn_remove.setEnabled(selected > 0)

    def _get_selected_apks(self):
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                info = item.data(Qt.ItemDataRole.UserRole)
                if info:
                    selected.append((row, info))
        return selected

    def _export_debloat_list(self):
        selected = self._get_selected_apks()
        if not selected:
            MessageBox("No Applications Selected", "Please select one or more applications to export.", self).exec()
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Debloat List", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for _, info in selected:
                        f.write(f"{info['package']}\n")
                MessageBox("Export Successful", f"Exported {len(selected)} packages to {os.path.basename(file_path)}.", self).exec()
            except Exception as e:
                MessageBox("Export Failed", f"Could not write file: {e}", self).exec()

    def _import_debloat_list(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Debloat List", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                target_packages = set(line.strip() for line in f if line.strip() and not line.startswith("#"))

            matched = 0
            self._updating_checks = True
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                pkg_item = self.table.item(row, 2)
                if item and pkg_item and pkg_item.text() in target_packages:
                    item.setCheckState(Qt.CheckState.Checked)
                    matched += 1
            self._updating_checks = False
            self._update_counter()

            MessageBox("Debloat List Imported", f"Found and selected {matched} matching application(s).", self).exec()
        except Exception as e:
            MessageBox("Import Failed", f"Could not read debloat list: {e}", self).exec()

    def _remove_selected(self):
        selected = self._get_selected_apks()
        if not selected:
            return

        box = MessageBox(
            "Confirm Application Removal",
            f"Are you sure you want to delete {len(selected)} selected application(s) from the ROM workspace?\n"
            "This will delete the APK files from extracted partitions.",
            self
        )
        if not box.exec():
            return

        removed_count = 0
        rows_to_remove = []
        for row, info in selected:
            apk_path = info.get("path")
            if apk_path and os.path.exists(apk_path):
                try:
                    os.remove(apk_path)
                    parent_dir = os.path.dirname(apk_path)
                    if os.path.exists(parent_dir):
                        remaining = os.listdir(parent_dir)
                        if not remaining or all(f.endswith((".odex", ".vdex", ".art", ".prof")) for f in remaining):
                            shutil.rmtree(parent_dir, ignore_errors=True)
                    removed_count += 1
                    rows_to_remove.append(row)
                except Exception as e:
                    logging.warning(f"Could not remove APK {apk_path}: {e}")

        # Remove rows from table in reverse order
        self._updating_checks = True
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)
        self._updating_checks = False
        self._update_counter()

        self.status_lbl.setText(f"Successfully removed {removed_count} application(s).")
        self.status_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 500;")
        MessageBox("Debloat Complete", f"Successfully removed {removed_count} application(s) from the project.", self).exec()

    def closeEvent(self, event):
        self.worker.cancel()
        self.worker.wait(1000)
        super().closeEvent(event)
