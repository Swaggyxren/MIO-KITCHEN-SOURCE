#!/bin/env python3
# Copyright (C) 2022-2026 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import time
import traceback

sys_stdout = sys.stdout
sys_stderr = sys.stderr

class DevNull(object):
    def write(self, s):
        pass
    def flush(self):
        pass

if not sys.stdout:
    sys.stdout = DevNull()

if sys.version_info.major == 3 and sys.version_info.minor < 8:
    input(f"Not supported: [{sys.version}] yet\nEnter to quit\nSorry for any inconvenience caused")
    sys.exit(1)

_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_root, "src")
_core = os.path.join(_src, "core")
_qt = os.path.join(_src, "qt_layer")
for _dir in (_root, _src, _core, _qt):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

try:
    from src.qt_layer.tool import *
    if __name__ == "__main__":
        init(sys.argv)
except Exception as e:
    # 1. Capture and log crash
    err_text = traceback.format_exc()
    exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else _root
    log_targets = [
        os.path.join(exe_dir, "crash.log"),
        os.path.expanduser("~/mio_kitchen_crash.log"),
        "/tmp/mio_kitchen_crash.log"
    ]
    for lp in log_targets:
        try:
            with open(lp, "w", encoding="utf-8") as f:
                f.write(err_text)
            break
        except Exception:
            pass

    # 3. Output to stderr if available
    try:
        if sys_stderr:
            sys_stderr.write(err_text + "\n")
            sys_stderr.flush()
    except Exception:
        pass

    # 4. Display graphical error dialog
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        _app = QApplication.instance() or QApplication([])
        QMessageBox.critical(
            None,
            "MIO-KITCHEN Startup Error",
            f"Application failed to start:\n\n{e}\n\nFull log saved to:\n{os.path.join(exe_dir, 'crash.log')}"
        )
    except Exception:
        pass

    sys.exit(1)