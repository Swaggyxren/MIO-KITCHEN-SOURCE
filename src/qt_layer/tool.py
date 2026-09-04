import os
import sys
import time
import warnings

import logging
from PySide6.QtCore import Qt, QTimer, QSize, QPoint, QEvent, QObject
from PySide6.QtGui import QIcon, QGuiApplication, QCursor
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (NavigationItemPosition, SplashScreen, setTheme, Theme,
                            FluentWindow, FluentIcon as FIF)

_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_src_dir)
_core_dir = os.path.join(_src_dir, "core")
for _p in (_root_dir, _src_dir, _core_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.qt_layer.plugins import PluginPage
from src.qt_layer.projects import ProjectsPage
from src.qt_layer.settings import SettingsPage
from src.qt_layer.about import AboutPage
from src.qt_layer.home import HomePage
from utils import temp, v_code

if sys.platform == "linux" or sys.platform == "linux2":
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Patch QFluentWidgets popup menus on Linux to eliminate black box artifacts and mask glitches
    try:
        from qfluentwidgets import RoundMenu, MenuAnimationType
        from qfluentwidgets.components.widgets.combo_box import ComboBox
        from PySide6.QtGui import QAction

        old_round_menu_init = RoundMenu._RoundMenu__initWidgets

        def linux_round_menu_init(self):
            old_round_menu_init(self)
            self.view.setGraphicsEffect(None)
            self.hBoxLayout.setContentsMargins(2, 2, 2, 2)

        RoundMenu._RoundMenu__initWidgets = linux_round_menu_init

        old_round_menu_exec = RoundMenu.exec

        def linux_round_menu_exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
            self.view.setGraphicsEffect(None)
            self.hBoxLayout.setContentsMargins(2, 2, 2, 2)
            return old_round_menu_exec(self, pos, ani=False, aniType=MenuAnimationType.NONE)

        RoundMenu.exec = linux_round_menu_exec

        def linux_show_combo_menu(self):
            if not self.items:
                return

            menu = self._createComboMenu()
            for item in self.items:
                action = QAction(item.icon, item.text)
                action.setEnabled(item.isEnabled)
                menu.addAction(action)

            menu.view.itemClicked.connect(lambda i: self._onItemClicked(self.findText(i.text().lstrip())))

            if menu.view.width() < self.width():
                menu.view.setMinimumWidth(self.width())
                menu.adjustSize()

            menu.setMaxVisibleItems(self.maxVisibleItems())
            menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            menu.closedSignal.connect(self._onDropMenuClosed)
            self.dropMenu = menu

            if self.currentIndex() >= 0 and self.items:
                menu.setDefaultAction(menu.actions()[self.currentIndex()])

            menu.view.setGraphicsEffect(None)
            menu.hBoxLayout.setContentsMargins(2, 2, 2, 2)
            pos = self.mapToGlobal(QPoint(0, self.height() + 2))
            menu.exec(pos, ani=False, aniType=MenuAnimationType.NONE)

        ComboBox._showComboMenu = linux_show_combo_menu
    except Exception as e:
        logging.warning(f"Could not apply Linux menu patch: {e}")

class TitleBarEventFilter(QObject):
    """Event filter for title bar dragging"""
    
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.m_drag = False
        self.m_dragPosition = QPoint()
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.m_drag = True
                self.m_dragPosition = event.globalPos() - self.window.frameGeometry().topLeft()
                obj.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                return True
        
        elif event.type() == QEvent.MouseMove:
            if self.m_drag and event.buttons() == Qt.MouseButton.LeftButton:
                self.window.move(event.globalPos() - self.m_dragPosition)
                return True
            else:
                obj.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        
        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                self.m_drag = False
                obj.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                return True
        
        elif event.type() == QEvent.Leave:
            obj.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        
        return False


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # Suppress window opacity warnings on Linux
        warnings.filterwarnings('ignore', message='.*opacity.*')

        # 设置主题
        setTheme(Theme.AUTO)

        # Prototype logo (accent blue badge with crisp bold white 'M')
        logo_path = 'bin/logo.png' if os.path.exists('bin/logo.png') else 'icon.ico'
        self.setWindowIcon(QIcon(logo_path))
        
        # Create splash screen with error handling
        try:
            self.splashScreen = SplashScreen(self.windowIcon(), self)
            self.splashScreen.setIconSize(QSize(140, 140))
        except Exception as e:
            # If splash screen fails due to opacity, just continue
            print(f"Warning: SplashScreen creation skipped ({e})")
            self.splashScreen = None
        
        self.show()

        # 设置窗口标题
        self.setWindowTitle("MIO-KITCHEN")

        # Title bar styling matching prototype layout
        self.titleBar.setIcon(self.windowIcon())
        self.titleBar.hBoxLayout.setContentsMargins(12, 0, 0, 0)
        self.titleBar.hBoxLayout.setSpacing(8)

        # 设置窗口大小
        self.resize(1000, 700)

        # 窗口居中显示
        self.center()

        # Install event filter on title bar for dragging
        self.title_bar_filter = TitleBarEventFilter(self)
        self.titleBar.installEventFilter(self.title_bar_filter)
        self.titleBar.setMouseTracking(True)

        # 创建页面
        self.home_page = HomePage()
        self.project_page = ProjectsPage()
        self.plugin_page = PluginPage()
        self.about_page = AboutPage()
        self.settings_page = SettingsPage()

        # 初始化导航
        self.initNavigation()

        # Finish splash screen if it was created
        if self.splashScreen:
            QTimer.singleShot(1000, self.splashScreen.finish)

    def center(self):
        desktop = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = desktop.width()
        screen_height = desktop.height()
        x = (screen_width - self.width()) // 2
        y = (screen_height - self.height()) // 2
        self.move(x, y)

    def initNavigation(self):
        # Add navigation items
        self.addSubInterface(self.home_page, FIF.HOME, 'Home')
        self.addSubInterface(self.project_page, FIF.DOCUMENT, 'Projects')
        self.addSubInterface(self.plugin_page, FIF.APPLICATION, 'Plugins')
        self.addSubInterface(self.about_page, FIF.INFO, 'About', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settings_page, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # Connect Home page quick launchpad actions
        self.home_page.quick_open_project.connect(lambda: self.switchTo(self.project_page))
        self.home_page.quick_new_project.connect(self._on_quick_new_project)
        self.home_page.quick_unpack_file.connect(self._on_quick_unpack_file)
        self.home_page.quick_manage_plugins.connect(lambda: self.switchTo(self.plugin_page))

        # Default display Home
        self.switchTo(self.home_page)

    def switchTo(self, interface):
        super().switchTo(interface)
        name = interface.objectName() if hasattr(interface, 'objectName') else str(interface)
        print(f"[NAVIGATE] Switched to view: {name}", flush=True)
        logging.info(f"[NAVIGATE] Switched to view: {name}")

    def _on_quick_new_project(self):
        print("[ACTION] Triggered Quick Action: New Project", flush=True)
        self.switchTo(self.project_page)
        self.project_page.show_create_dialog()

    def _on_quick_unpack_file(self):
        print("[ACTION] Triggered Quick Action: Unpack File", flush=True)
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ROM or Partition Image",
            "",
            "ROM Files (*.zip *.bin *.img *.ozip *.ofp *.ops *.pac *.cpb *.tar *.kdz);;All Files (*)"
        )
        if file_path:
            print(f"[ACTION] Selected ROM file to unpack: {file_path}", flush=True)
            self.switchTo(self.project_page)
            self.project_page.dndfile([file_path])


def __init__qt(args):
    os.makedirs(temp, exist_ok=True)
    tool_log = f'{temp}/{time.strftime("%Y%m%d_%H-%M-%S", time.localtime())}_{v_code()}.log'
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    app = QApplication(args)

    # Configure dual-output verbose logging (stdout + file)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', '%H:%M:%S')
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(tool_log, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)

    print("==================================================", flush=True)
    print("=== MIO-KITCHEN Verbose Engine Started ===", flush=True)
    print(f"=== Log File: {tool_log} ===", flush=True)
    print("==================================================", flush=True)

    window = MainWindow()
    window.show()
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass
    sys.exit(app.exec())


init = lambda args: __init__qt(args)
if __name__ == '__main__':
    init(sys.argv)
