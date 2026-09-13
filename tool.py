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

import signal

try:
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except Exception:
    pass

class SafeStream(object):
    def __init__(self, stream):
        self._stream = stream

    def write(self, s):
        try:
            if self._stream:
                return self._stream.write(s)
        except (BrokenPipeError, IOError, OSError, ValueError):
            pass

    def flush(self):
        try:
            if self._stream:
                return self._stream.flush()
        except (BrokenPipeError, IOError, OSError, ValueError):
            pass

    def __getattr__(self, name):
        return getattr(self._stream, name)

sys_stdout = sys.stdout
sys_stderr = sys.stderr

if sys.stdout:
    sys.stdout = SafeStream(sys.stdout)
else:
    sys.stdout = SafeStream(None)

if sys.stderr:
    sys.stderr = SafeStream(sys.stderr)
else:
    sys.stderr = SafeStream(None)

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

if sys.platform.startswith("linux"):
    if "QT_QPA_PLATFORM" not in os.environ and os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    import ctypes
    for _lib in (
        "/usr/lib/libxkbcommon.so.0",
        "/usr/lib64/libxkbcommon.so.0",
        "/usr/lib/x86_64-linux-gnu/libxkbcommon.so.0",
        "/usr/lib/aarch64-linux-gnu/libxkbcommon.so.0",
    ):
        if os.path.exists(_lib):
            try:
                ctypes.CDLL(_lib, mode=ctypes.RTLD_GLOBAL)
                break
            except Exception:
                pass
    for _lib in (
        "/usr/lib/libxkbcommon-x11.so.0",
        "/usr/lib64/libxkbcommon-x11.so.0",
        "/usr/lib/x86_64-linux-gnu/libxkbcommon-x11.so.0",
        "/usr/lib/aarch64-linux-gnu/libxkbcommon-x11.so.0",
    ):
        if os.path.exists(_lib):
            try:
                ctypes.CDLL(_lib, mode=ctypes.RTLD_GLOBAL)
                break
            except Exception:
                pass

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